// linux/arch/i386/kernel/time.c

#include <linux/errno.h>
#include <linux/sched.h>
#include <linux/kernel.h>
#include <linux/param.h>
#include <linux/string.h>
#include <linux/mm.h>
#include <linux/interrupt.h>
#include <linux/time.h>
#include <linux/delay.h>
#include <linux/init.h>
#include <linux/smp.h>

#include <asm/io.h>
#include <asm/smp.h>
#include <asm/irq.h>
#include <asm/msr.h>
#include <asm/delay.h>
#include <asm/mpspec.h>
#include <asm/uaccess.h>
#include <asm/processor.h>

#include <linux/mc146818rtc.h>
#include <linux/timex.h>
#include <linux/config.h>

#include <asm/fixmap.h>
#include <asm/cobalt.h>

/*
 * for x86_do_profile()
 */
#include <linux/irq.h>


unsigned long cpu_khz;	/* Detected as we calibrate the TSC */

/* Number of usecs that the last interrupt was delayed */
static int delay_at_last_interrupt;

static unsigned long last_tsc_low; /* lsb 32 bits of Time Stamp Counter */

/* Cached *multiplier* to convert TSC counts to microseconds.
 * (see the equation below).
 * Equal to 2^32 * (1 / (clocks per usec) ).
 * Initialized in time_init.
 */
unsigned long fast_gettimeoffset_quotient;

extern rwlock_t xtime_lock;
extern unsigned long wall_jiffies;

spinlock_t rtc_lock = SPIN_LOCK_UNLOCKED;

static inline unsigned long do_fast_gettimeoffset(void)
{
	register unsigned long eax, edx;

	/* Read the Time Stamp Counter */

	rdtsc(eax,edx);

	/* .. relative to previous jiffy (32 bits is enough) */
	eax -= last_tsc_low;	/* tsc_low delta */

	/*
         * Time offset = (tsc_low delta) * fast_gettimeoffset_quotient
         *             = (tsc_low delta) * (usecs_per_clock)
         *             = (tsc_low delta) * (usecs_per_jiffy / clocks_per_jiffy)
	 *
	 * Using a mull instead of a divl saves up to 31 clock cycles
	 * in the critical path.
         */

	__asm__("mull %2"
		:"=a" (eax), "=d" (edx)
		:"rm" (fast_gettimeoffset_quotient),
		 "0" (eax));

	/* our adjusted time offset in microseconds */
	return delay_at_last_interrupt + edx;
}

#define TICK_SIZE tick

spinlock_t i8253_lock = SPIN_LOCK_UNLOCKED;

extern spinlock_t i8259A_lock;

#ifndef CONFIG_X86_TSC

/* This function must be called with interrupts disabled 
 * It was inspired by Steve McCanne's microtime-i386 for BSD.  -- jrs
 * 
 * However, the pc-audio speaker driver changes the divisor so that
 * it gets interrupted rather more often - it loads 64 into the
 * counter rather than 11932! This has an adverse impact on
 * do_gettimeoffset() -- it stops working! What is also not
 * good is that the interval that our timer function gets called
 * is no longer 10.0002 ms, but 9.9767 ms. To get around this
 * would require using a different timing source. Maybe someone
 * could use the RTC - I know that this can interrupt at frequencies
 * ranging from 8192Hz to 2Hz. If I had the energy, I'd somehow fix
 * it so that at startup, the timer code in sched.c would select
 * using either the RTC or the 8253 timer. The decision would be
 * based on whether there was any other device around that needed
 * to trample on the 8253. I'd set up the RTC to interrupt at 1024 Hz,
 * and then do some jiggery to have a version of do_timer that 
 * advanced the clock by 1/1024 s. Every time that reached over 1/100
 * of a second, then do all the old code. If the time was kept correct
 * then do_gettimeoffset could just return 0 - there is no low order
 * divider that can be accessed.
 *
 * Ideally, you would be able to use the RTC for the speaker driver,
 * but it appears that the speaker driver really needs interrupt more
 * often than every 120 us or so.
 *
 * Anyway, this needs more thought....		pjsg (1993-08-28)
 * 
 * If you are really that interested, you should be reading
 * comp.protocols.time.ntp!
 */

static unsigned long do_slow_gettimeoffset(void)
{
	int count;

	static int count_p = LATCH;    /* for the first call after boot */
	static unsigned long jiffies_p = 0;

	/*
	 * cache volatile jiffies temporarily; we have IRQs turned off. 
	 */
	unsigned long jiffies_t;

	/* gets recalled with irq locally disabled */
	spin_lock(&i8253_lock);
	/* timer count may underflow right here */
	outb_p(0x00, 0x43);	/* latch the count ASAP */

	count = inb_p(0x40);	/* read the latched count */

	/*
	 * We do this guaranteed double memory access instead of a _p 
	 * postfix in the previous port access. Wheee, hackady hack
	 */
 	jiffies_t = jiffies;

	count |= inb_p(0x40) << 8;
	
        /* VIA686a test code... reset the latch if count > max + 1 */
        if (count > LATCH) {
                outb_p(0x34, 0x43);
                outb_p(LATCH & 0xff, 0x40);
                outb(LATCH >> 8, 0x40);
                count = LATCH - 1;
        }
	
	spin_unlock(&i8253_lock);

	/*
	 * avoiding timer inconsistencies (they are rare, but they happen)...
	 * there are two kinds of problems that must be avoided here:
	 *  1. the timer counter underflows
	 *  2. hardware problem with the timer, not giving us continuous time,
	 *     the counter does small "jumps" upwards on some Pentium systems,
	 *     (see c't 95/10 page 335 for Neptun bug.)
	 */

/* you can safely undefine this if you don't have the Neptune chipset */

#define BUGGY_NEPTUN_TIMER

	if( jiffies_t == jiffies_p ) {
		if( count > count_p ) {
			/* the nutcase */

			int i;

			spin_lock(&i8259A_lock);
			/*
			 * This is tricky when I/O APICs are used;
			 * see do_timer_interrupt().
			 */
			i = inb(0x20);
			spin_unlock(&i8259A_lock);

			/* assumption about timer being IRQ0 */
			if (i & 0x01) {
				/*
				 * We cannot detect lost timer interrupts ... 
				 * well, that's why we call them lost, don't we? :)
				 * [hmm, on the Pentium and Alpha we can ... sort of]
				 */
				count -= LATCH;
			} else {
#ifdef BUGGY_NEPTUN_TIMER
				/*
				 * for the Neptun bug we know that the 'latch'
				 * command doesnt latch the high and low value
				 * of the counter atomically. Thus we have to 
				 * substract 256 from the counter 
				 * ... funny, isnt it? :)
				 */

				count -= 256;
#else
				printk("do_slow_gettimeoffset(): hardware timer problem?\n");
#endif
			}
		}
	} else
		jiffies_p = jiffies_t;

	count_p = count;

	count = ((LATCH-1) - count) * TICK_SIZE;
	count = (count + LATCH/2) / LATCH;

	return count;
}

static unsigned long (*do_gettimeoffset)(void) = do_slow_gettimeoffset;

#else

#define do_gettimeoffset()	do_fast_gettimeoffset()

#endif

/*
 * This version of gettimeofday has microsecond resolution
 * and better than microsecond precision on fast x86 machines with TSC.
 */
void do_gettimeofday(struct timeval *tv)
{
	unsigned long flags;
	unsigned long usec, sec;

	read_lock_irqsave(&xtime_lock, flags);
	usec = do_gettimeoffset();
	{
		unsigned long lost = jiffies - wall_jiffies;
		if (lost)
			usec += lost * (1000000 / HZ);
	}
	sec = xtime.tv_sec;
	usec += xtime.tv_usec;
	read_unlock_irqrestore(&xtime_lock, flags);

	while (usec >= 1000000) {
		usec -= 1000000;
		sec++;
	}

	tv->tv_sec = sec;
	tv->tv_usec = usec;
}

void do_settimeofday(struct timeval *tv)
{
	write_lock_irq(&xtime_lock);
	/*
	 * This is revolting. We need to set "xtime" correctly. However, the
	 * value in this location is the value at the most recent update of
	 * wall time.  Discover what correction gettimeofday() would have
	 * made, and then undo it!
	 */
	tv->tv_usec -= do_gettimeoffset();
	tv->tv_usec -= (jiffies - wall_jiffies) * (1000000 / HZ);

	while (tv->tv_usec < 0) {
		tv->tv_usec += 1000000;
		tv->tv_sec--;
	}

	xtime = *tv;
	time_adjust = 0;		/* stop active adjtime() */
	time_status |= STA_UNSYNC;
	time_maxerror = NTP_PHASE_LIMIT;
	time_esterror = NTP_PHASE_LIMIT;
	write_unlock_irq(&xtime_lock);
}

/*
 * In order to set the CMOS clock precisely, set_rtc_mmss has to be
 * called 500 ms after the second nowtime has started, because when
 * nowtime is written into the registers of the CMOS clock, it will
 * jump to the next second precisely 500 ms later. Check the Motorola
 * MC146818A or Dallas DS12887 data sheet for details.
 *
 * BUG: This routine does not handle hour overflow properly; it just
 *      sets the minutes. Usually you'll only notice that after reboot!
 */
static int set_rtc_mmss(unsigned long nowtime)
{
	int retval = 0;
	int real_seconds, real_minutes, cmos_minutes;
	unsigned char save_control, save_freq_select;

	/* gets recalled with irq locally disabled */
	spin_lock(&rtc_lock);
	save_control = CMOS_READ(RTC_CONTROL); /* tell the clock it's being set */
	CMOS_WRITE((save_control|RTC_SET), RTC_CONTROL);

	save_freq_select = CMOS_READ(RTC_FREQ_SELECT); /* stop and reset prescaler */
	CMOS_WRITE((save_freq_select|RTC_DIV_RESET2), RTC_FREQ_SELECT);

	cmos_minutes = CMOS_READ(RTC_MINUTES);
	if (!(save_control & RTC_DM_BINARY) || RTC_ALWAYS_BCD)
		BCD_TO_BIN(cmos_minutes);

	/*
	 * since we're only adjusting minutes and seconds,
	 * don't interfere with hour overflow. This avoids
	 * messing with unknown time zones but requires your
	 * RTC not to be off by more than 15 minutes
	 */
	real_seconds = nowtime % 60;
	real_minutes = nowtime / 60;
	if (((abs(real_minutes - cmos_minutes) + 15)/30) & 1)
		real_minutes += 30;		/* correct for half hour time zone */
	real_minutes %= 60;

	if (abs(real_minutes - cmos_minutes) < 30) {
		if (!(save_control & RTC_DM_BINARY) || RTC_ALWAYS_BCD) {
			BIN_TO_BCD(real_seconds);
			BIN_TO_BCD(real_minutes);
		}
		CMOS_WRITE(real_seconds,RTC_SECONDS);
		CMOS_WRITE(real_minutes,RTC_MINUTES);
	} else {
		printk(KERN_WARNING
		       "set_rtc_mmss: can't update from %d to %d\n",
		       cmos_minutes, real_minutes);
		retval = -1;
	}

	/* The following flags have to be released exactly in this order,
	 * otherwise the DS12887 (popular MC146818A clone with integrated
	 * battery and quartz) will not reset the oscillator and will not
	 * update precisely 500 ms later. You won't find this mentioned in
	 * the Dallas Semiconductor data sheets, but who believes data
	 * sheets anyway ...                           -- Markus Kuhn
	 */
	CMOS_WRITE(save_control, RTC_CONTROL);
	CMOS_WRITE(save_freq_select, RTC_FREQ_SELECT);
	spin_unlock(&rtc_lock);

	return retval;
}

/* last time the cmos clock got updated */
static long last_rtc_update;

int timer_ack;



// 处理中断的通用函数
static inline void do_timer_interrupt(int irq, void *dev_id, struct pt_regs *regs)
{
	// ACK
	#ifdef CONFIG_X86_IO_APIC 
		if (timer_ack) {
			spin_lock(&i8259A_lock);
			outb(0x0c, 0x20);
			inb(0x20);
			spin_unlock(&i8259A_lock);
		}
	#endif

	do_timer(regs); // 调用了通用的内核函数 do_timer


	// 性能分析
	// 看看中断发生时，CPU 正在执行哪行代码
	#ifndef CONFIG_X86_LOCAL_APIC 
		if (!user_mode(regs))
			x86_do_profile(regs->eip);
	#else
		if (!using_apic_timer)
			smp_local_timer_interrupt(regs);
	#endif

	// 把内存里的时间写回主板电池供电的芯片里
	if ((time_status & STA_UNSYNC) == 0 &&
	    xtime.tv_sec > last_rtc_update + 660 &&
	    xtime.tv_usec >= 500000 - ((unsigned) tick) / 2 &&
	    xtime.tv_usec <= 500000 + ((unsigned) tick) / 2) {
		if (set_rtc_mmss(xtime.tv_sec) == 0)
			last_rtc_update = xtime.tv_sec;
		else
			last_rtc_update = xtime.tv_sec - 600; /* do it again in 60 s */
	}
	    
}

static int use_tsc;


// 时钟中断处理，关键函数
static void timer_interrupt(int irq, void *dev_id, struct pt_regs *regs)
{
	int count;

	write_lock(&xtime_lock); // 写入锁定，防止打扰（其他程序不能来写）

	// 计算从硬件发出中断信号，到 CPU 真正执行这行代码的这段时间内
	// 时钟中断被延迟了多少微秒
	if (use_tsc)
	{
		// 调用rdtscl，记下“现在”这一瞬间的精确时间戳
		rdtscl(last_tsc_low);

		// 冻结并读取 8253 计时器 (PIT)
		spin_lock(&i8253_lock);
		outb_p(0x00, 0x43);       // 发送命令：立刻锁存当前的计数值
		count = inb_p(0x40);      // 读低8位
		count |= inb(0x40) << 8;  // 读高8位
		spin_unlock(&i8253_lock); // 解锁 8253 计时器

		count = ((LATCH-1) - count) * TICK_SIZE;
		delay_at_last_interrupt = (count + LATCH/2) / LATCH; // 算出“迟到时间”
	}
 
	do_timer_interrupt(irq, NULL, regs); // 调用通用的时钟中断处理函数

	write_unlock(&xtime_lock); // 写入解锁，允许其他程序写入
}



// 初始化用，从CMOS/RTC芯片读取当前时间
unsigned long get_cmos_time(void)
{
	unsigned int year, mon, day, hour, min, sec;
	int i;

	spin_lock(&rtc_lock); // 访问CMOS硬件需要加锁 (rtc_lock)，因为它太慢了

	for (i = 0 ; i < 1000000 ; i++)	// 等待，直到UIP位为1 (表示更新正在进行)
		if (CMOS_READ(RTC_FREQ_SELECT) & RTC_UIP) // UIP指代“正在更新中”
			break;


	for (i = 0 ; i < 1000000 ; i++)	// 继续等待，直到UIP位为0 (表示更新刚刚完成，现在是读时间的最佳时机)
		if (!(CMOS_READ(RTC_FREQ_SELECT) & RTC_UIP))
			break;

	// 再次检查确保万无一失
	do { 
		sec = CMOS_READ(RTC_SECONDS);
		min = CMOS_READ(RTC_MINUTES);
		hour = CMOS_READ(RTC_HOURS);
		day = CMOS_READ(RTC_DAY_OF_MONTH);
		mon = CMOS_READ(RTC_MONTH);
		year = CMOS_READ(RTC_YEAR);
	} while (sec != CMOS_READ(RTC_SECONDS));

	// 如果是BCD编码，则转换为二进制. 将RTC硬件的“BCD码”翻译成内核认识的“二进制码”
	if (!(CMOS_READ(RTC_CONTROL) & RTC_DM_BINARY) || RTC_ALWAYS_BCD)
	  {
	    BCD_TO_BIN(sec);
	    BCD_TO_BIN(min);
	    BCD_TO_BIN(hour);
	    BCD_TO_BIN(day);
	    BCD_TO_BIN(mon);
	    BCD_TO_BIN(year);
	  }

	// 与“Y2K”年份修正
	spin_unlock(&rtc_lock);
	if ((year += 1900) < 1970)
		year += 100;
	return mktime(year, mon, day, hour, min, sec);
}

static struct irqaction irq0  = { timer_interrupt, SA_INTERRUPT, 0, "timer", NULL, NULL};


#define CALIBRATE_LATCH	(5 * LATCH)
#define CALIBRATE_TIME	(5 * 1000020/HZ)



// 用一个已知的慢时钟(PIT)，去测量一个未知的快时钟(TSC)，从而计算出CPU的准确频率
static unsigned long __init calibrate_tsc(void)
{
    // 初始化PIT的通道2，用于校准TSC，不要喇叭
	outb((inb(0x61) & ~0x02) | 0x01, 0x61);

	// 发送命令：你好，通道2 (10)，请准备好接收一个16位的LSB/MSB (11)数据，你将工作在模式0 (000，倒计时结束就停止)，并且使用二进制 (0) 计数
	outb(0xb0, 0x43);

	// 把 CALIBRATE_LATCH 这个16位的计数值（先发低8位，再发高8位）写入PIT，后面立刻开始倒计时
	outb(CALIBRATE_LATCH & 0xff, 0x42);
	outb(CALIBRATE_LATCH >> 8, 0x42);

	// 现在裁判（内核）要同时给选手（TSC）计时
	{
		unsigned long startlow, starthigh;
		unsigned long endlow, endhigh;
		unsigned long count;
		
		// “发令枪”：记录TSC起跑时间
		rdtsc(startlow,starthigh); 

		count = 0;

		// “等待”：内核盯着终点线，直到50毫秒结束
		do {
			count++;
		} while ((inb(0x61) & 0x20) == 0);

		// “冲线”：立刻记录TSC冲线时间
		rdtsc(endlow,endhigh);

		last_tsc_low = endlow;

		// 错误检查，确保比赛有效
		if (count <= 1)
			goto bad_ctc;

		// endlow 变量（因为 endhigh 预期为0）现在存储了“在这50毫秒内，TSC（快时钟）一共跳了多少下”
		__asm__("subl %2,%0\n\t"
			"sbbl %3,%1"
			:"=a" (endlow), "=d" (endhigh)
			:"g" (startlow), "g" (starthigh),
			 "0" (endlow), "1" (endhigh));

		// 错误处理，跳的太快，无法处理
		if (endhigh)
			goto bad_ctc;

		// 错误处理，跳的太man，无法处理
		if (endlow <= CALIBRATE_TIME)
			goto bad_ctc;

		// 现在计算出“每跳TSC需要多少微秒”
		__asm__("divl %2"
			:"=a" (endlow), "=d" (endhigh)
			:"r" (endlow), "0" (0), "1" (CALIBRATE_TIME));

		return endlow;
	}
bad_ctc: // 失败出口
	return 0;
}



// ************************************* //
// 从这里开始初始化
void __init time_init(void) 
{
	extern int x86_udelay_tsc;

    // 从硬件RTC读取当前时间
    // xtime 用于存放当前的wall time (自1970年1月1日以来的秒数和微秒数)
    // get_cmos_time() 是一个架构相关的函数，它会去访问CMOS/RTC芯片

	xtime.tv_sec = get_cmos_time();
	xtime.tv_usec = 0;
 
 	dodgy_tsc(); // 检查是否有不稳定的TSC (时间戳计数器)
 	
	if (cpu_has_tsc) {
		unsigned long tsc_quotient = calibrate_tsc(); // 校准TSC
		if (tsc_quotient) { // 如果校准成功
			fast_gettimeoffset_quotient = tsc_quotient; // 计算转换系数
			use_tsc = 1;
			x86_udelay_tsc = 1; // 允许 udelay() (微秒延迟函数) 也使用TSC

#ifndef do_gettimeoffset
			do_gettimeoffset = do_fast_gettimeoffset; // 使用基于TSC的快速的时间偏移计算函数，而非预设的慢速do_slow_gettimeoffset
#endif

	
            // 根据校准结果计算并报告CPU频率
			{	unsigned long eax=0, edx=1000;
				__asm__("divl %2"
		       		:"=a" (cpu_khz), "=d" (edx)
        	       		:"r" (tsc_quotient),
	                	"0" (eax), "1" (edx));
				printk("Detected %lu.%03lu MHz processor.\n", cpu_khz / 1000, cpu_khz % 1000);
			}
		}
	}

#ifdef CONFIG_VISWS
	printk("Starting Cobalt Timer system clock\n");

	/* Set the countdown value */
	co_cpu_write(CO_CPU_TIMEVAL, CO_TIME_HZ/HZ);

	/* Start the timer */
	co_cpu_write(CO_CPU_CTRL, co_cpu_read(CO_CPU_CTRL) | CO_CTRL_TIMERUN);

	/* Enable (unmask) the timer interrupt */
	co_cpu_write(CO_CPU_CTRL, co_cpu_read(CO_CPU_CTRL) & ~CO_CTRL_TIMEMASK);

	/* Wire cpu IDT entry to s/w handler (and Cobalt APIC to IDT) */
	setup_irq(CO_IRQ_TIMER, &irq0);
#else
	setup_irq(0, &irq0); // 注册时钟中断
#endif
}