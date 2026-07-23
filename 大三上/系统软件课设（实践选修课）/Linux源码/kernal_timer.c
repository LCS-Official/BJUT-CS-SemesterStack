// linux/kernel/timer.c


#include <linux/config.h>
#include <linux/mm.h>
#include <linux/timex.h>
#include <linux/delay.h>
#include <linux/smp_lock.h>
#include <linux/interrupt.h>
#include <linux/kernel_stat.h>

#include <asm/uaccess.h>

/*
 * Timekeeping variables
 */

long tick = (1000000 + HZ/2) / HZ;	/* timer interrupt period */

/* The current time */
struct timeval xtime __attribute__ ((aligned (16)));

/* Don't completely fail for HZ > 500.  */
int tickadj = 500/HZ ? : 1;		/* microsecs */

DECLARE_TASK_QUEUE(tq_timer);
DECLARE_TASK_QUEUE(tq_immediate);

/*
 * phase-lock loop variables
 */
/* TIME_ERROR prevents overwriting the CMOS clock */
int time_state = TIME_OK;		/* clock synchronization status	*/
int time_status = STA_UNSYNC;		/* clock status bits		*/
long time_offset;			/* time adjustment (us)		*/
long time_constant = 2;			/* pll time constant		*/
long time_tolerance = MAXFREQ;		/* frequency tolerance (ppm)	*/
long time_precision = 1;		/* clock precision (us)		*/
long time_maxerror = NTP_PHASE_LIMIT;	/* maximum error (us)		*/
long time_esterror = NTP_PHASE_LIMIT;	/* estimated error (us)		*/
long time_phase;			/* phase offset (scaled us)	*/
long time_freq = ((1000000 + HZ/2) % HZ - HZ/2) << SHIFT_USEC;
					/* frequency offset (scaled ppm)*/
long time_adj;				/* tick adjust (scaled 1 / HZ)	*/
long time_reftime;			/* time at last adjustment (s)	*/

long time_adjust;
long time_adjust_step;

unsigned long event;

extern int do_setitimer(int, struct itimerval *, struct itimerval *);

unsigned long volatile jiffies;

unsigned int * prof_buffer;
unsigned long prof_len;
unsigned long prof_shift;

/*
 * Event timer code
 */
#define TVN_BITS 6
#define TVR_BITS 8
#define TVN_SIZE (1 << TVN_BITS)
#define TVR_SIZE (1 << TVR_BITS)
#define TVN_MASK (TVN_SIZE - 1)
#define TVR_MASK (TVR_SIZE - 1)

struct timer_vec {
	int index;
	struct list_head vec[TVN_SIZE];
};

struct timer_vec_root {
	int index;
	struct list_head vec[TVR_SIZE];
};

static struct timer_vec tv5;
static struct timer_vec tv4;
static struct timer_vec tv3;
static struct timer_vec tv2;
static struct timer_vec_root tv1;

static struct timer_vec * const tvecs[] = {
	(struct timer_vec *)&tv1, &tv2, &tv3, &tv4, &tv5
};

#define NOOF_TVECS (sizeof(tvecs) / sizeof(tvecs[0]))

void init_timervecs (void)
{
	int i;

	for (i = 0; i < TVN_SIZE; i++) {
		INIT_LIST_HEAD(tv5.vec + i);
		INIT_LIST_HEAD(tv4.vec + i);
		INIT_LIST_HEAD(tv3.vec + i);
		INIT_LIST_HEAD(tv2.vec + i);
	}
	for (i = 0; i < TVR_SIZE; i++)
		INIT_LIST_HEAD(tv1.vec + i);
}

static unsigned long timer_jiffies;


// 根据定时器的到期时间 (expires) 和 当前处理进度 (timer_jiffies) 的差值
// 把定时器扔进 tv1 到 tv5 这五个轮子中合适的一个
static inline void internal_add_timer(struct timer_list *timer)
{

	unsigned long expires = timer->expires;
	unsigned long idx = expires - timer_jiffies;
	struct list_head * vec;

	// 决定把定时器放到哪一层
	if (idx < TVR_SIZE) { // 最近的任务 (tv1)
		int i = expires & TVR_MASK;
		vec = tv1.vec + i;
	} else if (idx < 1 << (TVR_BITS + TVN_BITS)) { // 稍远的任务 (tv2)
		int i = (expires >> TVR_BITS) & TVN_MASK;
		vec = tv2.vec + i;
	} else if (idx < 1 << (TVR_BITS + 2 * TVN_BITS)) { // 更远的任务 (tv3)
		int i = (expires >> (TVR_BITS + TVN_BITS)) & TVN_MASK;
		vec =  tv3.vec + i;
	} else if (idx < 1 << (TVR_BITS + 3 * TVN_BITS)) { // 很远的任务 (tv4)
		int i = (expires >> (TVR_BITS + 2 * TVN_BITS)) & TVN_MASK;
		vec = tv4.vec + i;
	} else if ((signed long) idx < 0) { // 卡住了，立刻插队
		vec = tv1.vec + tv1.index;
	} else if (idx <= 0xffffffffUL) { // 特别远的任务 (tv5)
		int i = (expires >> (TVR_BITS + 3 * TVN_BITS)) & TVN_MASK;
		vec = tv5.vec + i;
	} else { // 太遥远了 (64位系统兼容),不做处理
		INIT_LIST_HEAD(&timer->list);
		return;
	}

	list_add(&timer->list, vec->prev); // 入列 (FIFO)
}

/* Initialize both explicitly - let's try to have them in the same cache line */
spinlock_t timerlist_lock = SPIN_LOCK_UNLOCKED;

#ifdef CONFIG_SMP
volatile struct timer_list * volatile running_timer;
#define timer_enter(t) do { running_timer = t; mb(); } while (0)
#define timer_exit() do { running_timer = NULL; } while (0)
#define timer_is_running(t) (running_timer == t)
#define timer_synchronize(t) while (timer_is_running(t)) barrier()
#else
#define timer_enter(t)		do { } while (0)
#define timer_exit()		do { } while (0)
#endif

void add_timer(struct timer_list *timer)
{
	unsigned long flags;

	spin_lock_irqsave(&timerlist_lock, flags);
	if (timer_pending(timer))
		goto bug;
	internal_add_timer(timer);
	spin_unlock_irqrestore(&timerlist_lock, flags);
	return;
bug:
	spin_unlock_irqrestore(&timerlist_lock, flags);
	printk("bug: kernel timer added twice at %p.\n",
			__builtin_return_address(0));
}


// 从定时器链表中 摘除 指定定时器
static inline int detach_timer (struct timer_list *timer)
{
	if (!timer_pending(timer)) // 如果本来就没挂在链表上，就不用删了
		return 0;
	list_del(&timer->list); // 从双向链表中移除
	return 1;
}

int mod_timer(struct timer_list *timer, unsigned long expires)
{
	int ret;
	unsigned long flags;

	spin_lock_irqsave(&timerlist_lock, flags);
	timer->expires = expires;
	ret = detach_timer(timer);
	internal_add_timer(timer);
	spin_unlock_irqrestore(&timerlist_lock, flags);
	return ret;
}

int del_timer(struct timer_list * timer)
{
	int ret;
	unsigned long flags;

	spin_lock_irqsave(&timerlist_lock, flags);
	ret = detach_timer(timer);
	timer->list.next = timer->list.prev = NULL;
	spin_unlock_irqrestore(&timerlist_lock, flags);
	return ret;
}

#ifdef CONFIG_SMP
void sync_timers(void)
{
	spin_unlock_wait(&global_bh_lock);
}

/*
 * SMP specific function to delete periodic timer.
 * Caller must disable by some means restarting the timer
 * for new. Upon exit the timer is not queued and handler is not running
 * on any CPU. It returns number of times, which timer was deleted
 * (for reference counting).
 */

int del_timer_sync(struct timer_list * timer)
{
	int ret = 0;

	for (;;) {
		unsigned long flags;
		int running;

		spin_lock_irqsave(&timerlist_lock, flags);
		ret += detach_timer(timer);
		timer->list.next = timer->list.prev = 0;
		running = timer_is_running(timer);
		spin_unlock_irqrestore(&timerlist_lock, flags);

		if (!running)
			break;

		timer_synchronize(timer);
	}

	return ret;
}
#endif

// 负责在时针动的时候，把任务从时针盘搬到分针盘(级联表上不同的层级之间搬运任务)
static inline void cascade_timers(struct timer_vec *tv)
{

	struct list_head *head, *curr, *next;
	
	// 找到当前指针指向的那个格子
	head = tv->vec + tv->index;
	curr = head->next;
	
	// 遍历这个格子里的整条链表
	while (curr != head) {
		struct timer_list *tmp;

		// 拿到定时器对象
		tmp = list_entry(curr, struct timer_list, list);
		next = curr->next;

		// 从当前这一层的大轮子里移除
		list_del(curr); 
		
		// 重新添加定时器，把这个定时器放入下一层更精细的轮子
		internal_add_timer(tmp);
		curr = next;
	}
	INIT_LIST_HEAD(head); // 擦除痕迹，重置
	tv->index = (tv->index + 1) & TVN_MASK; // 指针前移
}


// 内核日程管理中心。使用时间轮算法
// 因为时间流逝了，所以内核需要检查有没有软件定时器到期了，如果有，就执行它
static inline void run_timer_list(void)
{

	spin_lock_irq(&timerlist_lock); // 内核同步原语，用于在获取自旋锁的同时禁止本地中断（从而避免死锁）

	// 循环条件：只要 timer_jiffies (上次处理的时间) 落后于 jiffies (当前系统时间)，
    // 就一直循环，一格一格地补上
	while ((long)(jiffies - timer_jiffies) >= 0) {	
		struct list_head *head, *curr;

		// 实现多级分层，每当最低层时间轮转一圈，就把更高一层的时间轮上对应槽的定时器级联下来（cascade）
		if (!tv1.index) {
			int n = 1;
			do {
				// 从下一层轮子（分针）里搬运任务下来
				cascade_timers(tvecs[n]);
			
			// 如果 tvecs[n] 也转了一圈 (index回到了1)，就继续向更高层索要任务。
            // 比如秒针转完找分针，分针转完找时针
			} while (tvecs[n]->index == 1 && ++n < NOOF_TVECS); 
		}
		repeat: // 和底下的goto配合使用，实现循环处理所有到期定时器

		// 定位到时间轮 tv1 当前刻度 (index) 对应的链表头
		head = tv1.vec + tv1.index;
		curr = head->next;

		// 只要链表不为空，当前时刻有任务要执行
		if (curr != head) {
			struct timer_list *timer;
			void (*fn)(unsigned long);
			unsigned long data;

			// 还原定时器结构：利用 list_entry 从链表指针推算出结构体首地址
			timer = list_entry(curr, struct timer_list, list);

			// 备份关键信息：因为执行完后 timer 结构体可能会被释放，必须先保存
 			fn = timer->function;
 			data= timer->data;
			
			// 摘除定时器：从时间轮链表中删除它，因为它是一次性的
			detach_timer(timer);

			// 将指针置空，防止野指针，也作为 timer_pending() 的判断依据
			timer->list.next = timer->list.prev = NULL;

			// SMP 保护: 标记该 timer 正在当前 CPU 上运行，防止其他 CPU 删除它
			timer_enter(timer);

			// 解锁，fn可能会执行很久，或者会休眠	
			spin_unlock_irq(&timerlist_lock); 

			fn(data); // 执行用户的任务

			// 恢复现场，重新上锁
			spin_lock_irq(&timerlist_lock); 

			timer_exit();

			// 必须回到 repeat 处，
            // 重新读取 head->next，看链表里剩下的第一个任务是谁
			goto repeat; 
		}
		// 指针前移，准备处理下一个时间刻度
		++timer_jiffies; 

		// 轮子指针转一格，& TVR_MASK 实现了 0-255 的循环回绕
		tv1.index = (tv1.index + 1) & TVR_MASK;
	}
	// 所有落下的时间都追平了，解锁并开中断，收工
	spin_unlock_irq(&timerlist_lock);
}

spinlock_t tqueue_lock = SPIN_LOCK_UNLOCKED;

void tqueue_bh(void)
{
	run_task_queue(&tq_timer);
}

void immediate_bh(void)
{
	run_task_queue(&tq_immediate);
}

/*
 * this routine handles the overflow of the microsecond field
 *
 * The tricky bits of code to handle the accurate clock support
 * were provided by Dave Mills (Mills@UDEL.EDU) of NTP fame.
 * They were originally developed for SUN and DEC kernels.
 * All the kudos should go to Dave for this stuff.
 *
 */
static void second_overflow(void)
{
    long ltemp;

    /* Bump the maxerror field */
    time_maxerror += time_tolerance >> SHIFT_USEC;
    if ( time_maxerror > NTP_PHASE_LIMIT ) {
	time_maxerror = NTP_PHASE_LIMIT;
	time_status |= STA_UNSYNC;
    }

    /*
     * Leap second processing. If in leap-insert state at
     * the end of the day, the system clock is set back one
     * second; if in leap-delete state, the system clock is
     * set ahead one second. The microtime() routine or
     * external clock driver will insure that reported time
     * is always monotonic. The ugly divides should be
     * replaced.
     */
    switch (time_state) {

    case TIME_OK:
	if (time_status & STA_INS)
	    time_state = TIME_INS;
	else if (time_status & STA_DEL)
	    time_state = TIME_DEL;
	break;

    case TIME_INS:
	if (xtime.tv_sec % 86400 == 0) {
	    xtime.tv_sec--;
	    time_state = TIME_OOP;
	    printk(KERN_NOTICE "Clock: inserting leap second 23:59:60 UTC\n");
	}
	break;

    case TIME_DEL:
	if ((xtime.tv_sec + 1) % 86400 == 0) {
	    xtime.tv_sec++;
	    time_state = TIME_WAIT;
	    printk(KERN_NOTICE "Clock: deleting leap second 23:59:59 UTC\n");
	}
	break;

    case TIME_OOP:
	time_state = TIME_WAIT;
	break;

    case TIME_WAIT:
	if (!(time_status & (STA_INS | STA_DEL)))
	    time_state = TIME_OK;
    }

    /*
     * Compute the phase adjustment for the next second. In
     * PLL mode, the offset is reduced by a fixed factor
     * times the time constant. In FLL mode the offset is
     * used directly. In either mode, the maximum phase
     * adjustment for each second is clamped so as to spread
     * the adjustment over not more than the number of
     * seconds between updates.
     */
    if (time_offset < 0) {
	ltemp = -time_offset;
	if (!(time_status & STA_FLL))
	    ltemp >>= SHIFT_KG + time_constant;
	if (ltemp > (MAXPHASE / MINSEC) << SHIFT_UPDATE)
	    ltemp = (MAXPHASE / MINSEC) << SHIFT_UPDATE;
	time_offset += ltemp;
	time_adj = -ltemp << (SHIFT_SCALE - SHIFT_HZ - SHIFT_UPDATE);
    } else {
	ltemp = time_offset;
	if (!(time_status & STA_FLL))
	    ltemp >>= SHIFT_KG + time_constant;
	if (ltemp > (MAXPHASE / MINSEC) << SHIFT_UPDATE)
	    ltemp = (MAXPHASE / MINSEC) << SHIFT_UPDATE;
	time_offset -= ltemp;
	time_adj = ltemp << (SHIFT_SCALE - SHIFT_HZ - SHIFT_UPDATE);
    }

    /*
     * Compute the frequency estimate and additional phase
     * adjustment due to frequency error for the next
     * second. When the PPS signal is engaged, gnaw on the
     * watchdog counter and update the frequency computed by
     * the pll and the PPS signal.
     */
    pps_valid++;
    if (pps_valid == PPS_VALID) {	/* PPS signal lost */
	pps_jitter = MAXTIME;
	pps_stabil = MAXFREQ;
	time_status &= ~(STA_PPSSIGNAL | STA_PPSJITTER |
			 STA_PPSWANDER | STA_PPSERROR);
    }
    ltemp = time_freq + pps_freq;
    if (ltemp < 0)
	time_adj -= -ltemp >>
	    (SHIFT_USEC + SHIFT_HZ - SHIFT_SCALE);
    else
	time_adj += ltemp >>
	    (SHIFT_USEC + SHIFT_HZ - SHIFT_SCALE);

#if HZ == 100
    /* Compensate for (HZ==100) != (1 << SHIFT_HZ).
     * Add 25% and 3.125% to get 128.125; => only 0.125% error (p. 14)
     */
    if (time_adj < 0)
	time_adj -= (-time_adj >> 2) + (-time_adj >> 5);
    else
	time_adj += (time_adj >> 2) + (time_adj >> 5);
#endif
}

/* in the NTP reference this is called "hardclock()" */
static void update_wall_time_one_tick(void)
{
	if ( (time_adjust_step = time_adjust) != 0 ) {
	    /* We are doing an adjtime thing. 
	     *
	     * Prepare time_adjust_step to be within bounds.
	     * Note that a positive time_adjust means we want the clock
	     * to run faster.
	     *
	     * Limit the amount of the step to be in the range
	     * -tickadj .. +tickadj
	     */
	     if (time_adjust > tickadj)
		time_adjust_step = tickadj;
	     else if (time_adjust < -tickadj)
		time_adjust_step = -tickadj;
	     
	    /* Reduce by this step the amount of time left  */
	    time_adjust -= time_adjust_step;
	}
	xtime.tv_usec += tick + time_adjust_step;
	/*
	 * Advance the phase, once it gets to one microsecond, then
	 * advance the tick more.
	 */
	time_phase += time_adj;
	if (time_phase <= -FINEUSEC) {
		long ltemp = -time_phase >> SHIFT_SCALE;
		time_phase += ltemp << SHIFT_SCALE;
		xtime.tv_usec -= ltemp;
	}
	else if (time_phase >= FINEUSEC) {
		long ltemp = time_phase >> SHIFT_SCALE;
		time_phase -= ltemp << SHIFT_SCALE;
		xtime.tv_usec += ltemp;
	}
}

/*
 * Using a loop looks inefficient, but "ticks" is
 * usually just one (we shouldn't be losing ticks,
 * we're doing this this way mainly for interrupt
 * latency reasons, not because we think we'll
 * have lots of lost timer ticks
 */
static void update_wall_time(unsigned long ticks)
{
	do {
		ticks--;
		update_wall_time_one_tick();
	} while (ticks);

	if (xtime.tv_usec >= 1000000) {
	    xtime.tv_usec -= 1000000;
	    xtime.tv_sec++;
	    second_overflow();
	}
}

static inline void do_process_times(struct task_struct *p,
	unsigned long user, unsigned long system)
{
	unsigned long psecs;

	psecs = (p->times.tms_utime += user);
	psecs += (p->times.tms_stime += system);
	if (psecs / HZ > p->rlim[RLIMIT_CPU].rlim_cur) {
		/* Send SIGXCPU every second.. */
		if (!(psecs % HZ))
			send_sig(SIGXCPU, p, 1);
		/* and SIGKILL when we go over max.. */
		if (psecs / HZ > p->rlim[RLIMIT_CPU].rlim_max)
			send_sig(SIGKILL, p, 1);
	}
}

static inline void do_it_virt(struct task_struct * p, unsigned long ticks)
{
	unsigned long it_virt = p->it_virt_value;

	if (it_virt) {
		it_virt -= ticks;
		if (!it_virt) {
			it_virt = p->it_virt_incr;
			send_sig(SIGVTALRM, p, 1);
		}
		p->it_virt_value = it_virt;
	}
}

static inline void do_it_prof(struct task_struct *p)
{
	unsigned long it_prof = p->it_prof_value;

	if (it_prof) {
		if (--it_prof == 0) {
			it_prof = p->it_prof_incr;
			send_sig(SIGPROF, p, 1);
		}
		p->it_prof_value = it_prof;
	}
}

// 统计单个进程在当前 CPU 上的运行时间，并检查相关的软硬件限制（“记账”工作）
void update_one_process(struct task_struct *p, unsigned long user,
			unsigned long system, int cpu)
{
	p->per_cpu_utime[cpu] += user;
	p->per_cpu_stime[cpu] += system;
	do_process_times(p, user, system); // 将时间累加到进程的总时间统计中

	//检查两种定时器
	do_it_virt(p, user);
	do_it_prof(p);
}	


// 调度与统计CPU时间使用情况
void update_process_times(int user_tick)
{
	struct task_struct *p = current;
	int cpu = smp_processor_id(), system = user_tick ^ 1;

	// 统计进程CPU使用时间等（“记账”工作）
	update_one_process(p, user_tick, system, cpu);

	if (p->pid) {
		if (--p->counter <= 0) { // 如果时间片用完了
			p->counter = 0; 
			p->need_resched = 1; // 贴上“需要调度”的标签
		}

		// 记录谁在用CPU（用户、nice和系统）
		if (p->nice > 0) 
			kstat.per_cpu_nice[cpu] += user_tick;
		else
			kstat.per_cpu_user[cpu] += user_tick;
		kstat.per_cpu_system[cpu] += system;
	} else if (local_bh_count(cpu) || local_irq_count(cpu) > 1) // 空闲进程
		kstat.per_cpu_system[cpu] += system;
}



/*
 * Nr of active tasks - counted in fixed-point numbers
 */
static unsigned long count_active_tasks(void)
{
	struct task_struct *p;
	unsigned long nr = 0;

	read_lock(&tasklist_lock);
	for_each_task(p) {
		if ((p->state == TASK_RUNNING ||
		     (p->state & TASK_UNINTERRUPTIBLE)))
			nr += FIXED_1;
	}
	read_unlock(&tasklist_lock);
	return nr;
}

/*
 * Hmm.. Changed this, as the GNU make sources (load.c) seems to
 * imply that avenrun[] is the standard name for this kind of thing.
 * Nothing else seems to be standardized: the fractional size etc
 * all seem to differ on different machines.
 */
unsigned long avenrun[3];


// 计算系统负载
static inline void calc_load(unsigned long ticks)
{
	unsigned long active_tasks;
	static int count = LOAD_FREQ; // 每隔 LOAD_FREQ 个时钟中断计算一次系统负载

	count -= ticks;
	if (count < 0) {
		count += LOAD_FREQ;
		active_tasks = count_active_tasks(); // 计算当前活跃任务数

		// 执行的是定点算术的指数衰减公式，更新系统负载值
		CALC_LOAD(avenrun[0], EXP_1, active_tasks);
		CALC_LOAD(avenrun[1], EXP_5, active_tasks);
		CALC_LOAD(avenrun[2], EXP_15, active_tasks);
	}
}

/* jiffies at the most recent update of wall time */
unsigned long wall_jiffies;

/*
 * This spinlock protect us from races in SMP while playing with xtime. -arca
 */
rwlock_t xtime_lock = RW_LOCK_UNLOCKED;



// 把 jiffies 的增量转换成人类可读的年月日时分秒
static inline void update_times(void)
{
	unsigned long ticks;

	write_lock_irq(&xtime_lock);

	// 机器节拍 -> 人类时间
	ticks = jiffies - wall_jiffies;
	if (ticks) {
		wall_jiffies += ticks;
		update_wall_time(ticks);
	}
	write_unlock_irq(&xtime_lock);

	// 计算系统负载
	calc_load(ticks);
}


// 定时器的底半部处理
void timer_bh(void)
{
	update_times();
	run_timer_list();
}



// 内核定时器中断处理程序
void do_timer(struct pt_regs *regs)
{
	(*(unsigned long *)&jiffies)++; // 增加 jiffies 计数器（系统心跳）

	#ifndef CONFIG_SMP // 对单核处理器作用，扣除当前用户的机时，没钱了就准备踢下线
		update_process_times(user_mode(regs));
	#endif

	mark_bh(TIMER_BH); // 标记定时器底半部任务队列需要运行

	if (TQ_ACTIVE(tq_timer)) // 如果定时器底半部任务队列有任务需要运行，也挂号
		mark_bh(TQUEUE_BH);
}




#if !defined(__alpha__) && !defined(__ia64__)

/*
 * For backwards compatibility?  This can be done in libc so Alpha
 * and all newer ports shouldn't need it.
 */
asmlinkage unsigned long sys_alarm(unsigned int seconds)
{
	struct itimerval it_new, it_old;
	unsigned int oldalarm;

	it_new.it_interval.tv_sec = it_new.it_interval.tv_usec = 0;
	it_new.it_value.tv_sec = seconds;
	it_new.it_value.tv_usec = 0;
	do_setitimer(ITIMER_REAL, &it_new, &it_old);
	oldalarm = it_old.it_value.tv_sec;
	/* ehhh.. We can't return 0 if we have an alarm pending.. */
	/* And we'd better return too much than too little anyway */
	if (it_old.it_value.tv_usec)
		oldalarm++;
	return oldalarm;
}

#endif

#ifndef __alpha__

/*
 * The Alpha uses getxpid, getxuid, and getxgid instead.  Maybe this
 * should be moved into arch/i386 instead?
 */
 
asmlinkage long sys_getpid(void)
{
	/* This is SMP safe - current->pid doesn't change */
	return current->tgid;
}

/*
 * This is not strictly SMP safe: p_opptr could change
 * from under us. However, rather than getting any lock
 * we can use an optimistic algorithm: get the parent
 * pid, and go back and check that the parent is still
 * the same. If it has changed (which is extremely unlikely
 * indeed), we just try again..
 *
 * NOTE! This depends on the fact that even if we _do_
 * get an old value of "parent", we can happily dereference
 * the pointer: we just can't necessarily trust the result
 * until we know that the parent pointer is valid.
 *
 * The "mb()" macro is a memory barrier - a synchronizing
 * event. It also makes sure that gcc doesn't optimize
 * away the necessary memory references.. The barrier doesn't
 * have to have all that strong semantics: on x86 we don't
 * really require a synchronizing instruction, for example.
 * The barrier is more important for code generation than
 * for any real memory ordering semantics (even if there is
 * a small window for a race, using the old pointer is
 * harmless for a while).
 */
asmlinkage long sys_getppid(void)
{
	int pid;
	struct task_struct * me = current;
	struct task_struct * parent;

	parent = me->p_opptr;
	for (;;) {
		pid = parent->pid;
#if CONFIG_SMP
{
		struct task_struct *old = parent;
		mb();
		parent = me->p_opptr;
		if (old != parent)
			continue;
}
#endif
		break;
	}
	return pid;
}

asmlinkage long sys_getuid(void)
{
	/* Only we change this so SMP safe */
	return current->uid;
}

asmlinkage long sys_geteuid(void)
{
	/* Only we change this so SMP safe */
	return current->euid;
}

asmlinkage long sys_getgid(void)
{
	/* Only we change this so SMP safe */
	return current->gid;
}

asmlinkage long sys_getegid(void)
{
	/* Only we change this so SMP safe */
	return  current->egid;
}

#endif

/* Thread ID - the internal kernel "pid" */
asmlinkage long sys_gettid(void)
{
	return current->pid;
}

asmlinkage long sys_nanosleep(struct timespec *rqtp, struct timespec *rmtp)
{
	struct timespec t;
	unsigned long expire;

	if(copy_from_user(&t, rqtp, sizeof(struct timespec)))
		return -EFAULT;

	if (t.tv_nsec >= 1000000000L || t.tv_nsec < 0 || t.tv_sec < 0)
		return -EINVAL;


	if (t.tv_sec == 0 && t.tv_nsec <= 2000000L &&
	    current->policy != SCHED_OTHER)
	{
		/*
		 * Short delay requests up to 2 ms will be handled with
		 * high precision by a busy wait for all real-time processes.
		 *
		 * Its important on SMP not to do this holding locks.
		 */
		udelay((t.tv_nsec + 999) / 1000);
		return 0;
	}

	expire = timespec_to_jiffies(&t) + (t.tv_sec || t.tv_nsec);

	current->state = TASK_INTERRUPTIBLE;
	expire = schedule_timeout(expire);

	if (expire) {
		if (rmtp) {
			jiffies_to_timespec(expire, &t);
			if (copy_to_user(rmtp, &t, sizeof(struct timespec)))
				return -EFAULT;
		}
		return -EINTR;
	}
	return 0;
}

