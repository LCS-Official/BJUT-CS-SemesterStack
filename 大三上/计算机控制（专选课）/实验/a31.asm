;====================================================================
; 实验3.3: 直流电机转速闭环控制 (完整版)
; 功能: 
;   1. 键盘输入期望转速(00-99 RPS)，显示在左侧。
;   2. 霍尔传感器测量实际转速，显示在右侧。
;   3. 每秒自动调整DAC输出，使实际转速追随期望转速。
;====================================================================

;--- 硬件地址定义 ---
; 基于 CS0 (08000H)
COM8255_BIT EQU 08002H   ; 位选/列扫描口 
COM8255_SEG EQU 08004H   ; 段码口 
KEY_IN_PORT EQU 08001H   ; 键盘行读入口 

; 基于 CS2 (0A000H)
DAC_PORT    EQU 0A000H   ; DAC0832地址 [cite: 270]

;--- 内存变量定义 ---
DISP_BUF    EQU 30H      ; 显示缓冲区 (30H-35H: 30/31=Target, 32/33=Black, 34/35=Actual)
TARGET_SPD  EQU 36H      ; 期望转速
ACTUAL_SPD  EQU 37H      ; 实际转速
DAC_VAL     EQU 38H      ; 当前DAC输出值
T0_COUNT    EQU 39H      ; 1秒计时器

;--- 复位与中断入口 ---
        ORG 0000H
        LJMP START

        ORG 000BH        ; T0中断入口 (定时控制)
        LJMP TIMER0_ISR

        ORG 0030H
START:
        MOV SP, #60H     ; 设置堆栈

        ;--- 1. 变量初始化 ---
        MOV TARGET_SPD, #20     ; 默认期望转速设为 20 转/秒
        MOV ACTUAL_SPD, #00
        MOV DAC_VAL, #80H       ; 初始给一半电压启动
        MOV T0_COUNT, #0
        
        ;--- 2. 定时器初始化 ---
        ; TMOD: T1=16位计数(C/T=1), T0=16位定时(C/T=0) -> 0101 0001 = 51H
        MOV TMOD, #51H
        
        ; T0: 50ms 定时 (12MHz晶振)
        ; 初值 = 65536 - 50000 = 15536 = 3CB0H
        MOV TH0, #3CH
        MOV TL0, #0B0H
        
        ; T1: 外部脉冲计数 (从0开始)
        MOV TH1, #00H
        MOV TL1, #00H
        
        ;--- 3. 启动系统 ---
        SETB TR0         ; 启动T0定时
        SETB TR1         ; 启动T1计数
        SETB ET0         ; 允许T0中断
        SETB EA          ; 开总中断

        ; 初始DAC输出
        MOV DPTR, #DAC_PORT
        MOV A, DAC_VAL
        MOVX @DPTR, A

MAIN_LOOP:
        ;--- 主循环任务A: 刷新显示数据 ---
        ACALL UPDATE_BUF     ; 将 Target/Actual 数值转为显存数据

        ;--- 主循环任务B: 动态扫描显示 (多次调用以防闪烁) ---
        MOV R6, #10          ; 扫描10轮
SCAN_LOOP:
        ACALL DISPLAY_SCAN
        DJNZ R6, SCAN_LOOP

        ;--- 主循环任务C: 键盘扫描 ---
        ACALL KEY_SCAN_FULL  ; 检测按键
        CJNE A, #0FFH, KEY_PROC
        SJMP MAIN_LOOP

KEY_PROC:
        ;--- 按键处理逻辑 ---
        ; 假设输入逻辑: 类似计算器，挤入最后一位
        ; New_Target = (Old_Target % 10) * 10 + Key_Value
        ; 这样可以输入 2 位数
        PUSH ACC             ; 保存键值(0-9)
        
        MOV A, TARGET_SPD
        MOV B, #10
        DIV AB               ; A=十位, B=个位
        MOV A, B             ; A = 旧个位
        MOV B, #10
        MUL AB               ; A = 旧个位 * 10
        MOV R2, A            ; 暂存
        
        POP ACC              ; 恢复键值
        ADD A, R2            ; A = (旧个位*10) + 新键值
        
        MOV TARGET_SPD, A    ; 更新期望值
        
        ACALL KEY_WAIT_REL   ; 等待按键释放
        SJMP MAIN_LOOP

;====================================================================
; 中断服务: TIMER0_ISR
; 频率: 每50ms触发一次
; 功能: 凑齐1秒后，计算转速并调整DAC
;====================================================================
TIMER0_ISR:
        PUSH ACC
        PUSH PSW
        PUSH DPH
        PUSH DPL
        
        ; 重装初值
        MOV TH0, #3CH
        MOV TL0, #0B0H
        
        INC T0_COUNT
        MOV A, T0_COUNT
        CJNE A, #20, ISR_END ; 是否满1秒 (20 * 50ms = 1000ms)
        
        ;=== 1秒时间到，执行控制算法 ===
        MOV T0_COUNT, #0     ; 清零计数
        
        ; 1. 读取实际转速 (T1计数值)
        CLR TR1              ; 暂停T1以免读数错误
        MOV A, TL1           ; 读低8位 (假设转速不超过255)
        MOV ACTUAL_SPD, A    ; 保存到变量
        MOV TH1, #0          ; 清空计数器
        MOV TL1, #0
        SETB TR1             ; 重启T1
        
        ; 2. 比较 实际值 vs 期望值
        MOV A, TARGET_SPD
        CLR C
        SUBB A, ACTUAL_SPD
        JZ ISR_DAC_OUT       ; 相等，不调整
        
        ; 判断 C 标志位
        ; 若 Target >= Actual (C=0): 速度不够 -> 加速
        ; 若 Target < Actual  (C=1): 速度太快 -> 减速
        JC SLOW_DOWN
        
SPEED_UP:
        ; 加速: 增加DAC值
        MOV A, DAC_VAL
        ADD A, #05H          ; 步长5 (可调: 越大反应越快但易震荡)
        JC MAX_LIMIT         ; 如果溢出(超过255)
        MOV DAC_VAL, A
        SJMP ISR_DAC_OUT
MAX_LIMIT:
        MOV DAC_VAL, #0FFH   ; 封顶
        SJMP ISR_DAC_OUT

SLOW_DOWN:
        ; 减速: 减小DAC值
        MOV A, DAC_VAL
        SUBB A, #05H         ; 步长5
        JNC MIN_LIMIT        ; 如果没有借位(结果正常)
        MOV DAC_VAL, #00H    ; 触底(小于0)
        SJMP ISR_DAC_OUT
MIN_LIMIT:
        MOV DAC_VAL, A

ISR_DAC_OUT:
        ; 3. 输出控制电压
        MOV DPTR, #DAC_PORT
        MOV A, DAC_VAL
        MOVX @DPTR, A

ISR_END:
        POP DPL
        POP DPH
        POP PSW
        POP ACC
        RETI

;====================================================================
; 子程序: 显示数据转换
; 将 HEX 变量拆分为 10进制显示码放入缓冲区
;====================================================================
UPDATE_BUF:
        ; 1. 处理期望值 (Target) -> LED5, LED4 (左)
        MOV A, TARGET_SPD
        MOV B, #10
        DIV AB
        MOV 30H, A           ; 十位
        MOV 31H, B           ; 个位
        
        ; 2. 中间黑屏 -> LED3, LED2
        MOV 32H, #10         ; 10对应全灭
        MOV 33H, #10
        
        ; 3. 处理实际值 (Actual) -> LED1, LED0 (右)
        MOV A, ACTUAL_SPD
        MOV B, #10
        DIV AB
        MOV 34H, A
        MOV 35H, B
        RET

;====================================================================
; 子程序: 动态扫描显示
;====================================================================
DISPLAY_SCAN:
        MOV R0, #30H         ; 缓冲首址
        MOV R2, #0FEH        ; 位选初值 (对应LED5)
        
DISP_NEXT:
        ; 输出位选
        MOV DPTR, #COM8255_BIT
        MOV A, R2
        MOVX @DPTR, A
        
        ; 查表取段码
        MOV A, @R0
        MOV DPTR, #SEG_TAB
        MOVC A, @A+DPTR
        
        ; 输出段码
        MOV DPTR, #COM8255_SEG
        MOVX @DPTR, A
        
        ; 延时并消隐
        ACALL DELAY_SMALL
        MOV A, #00H
        MOVX @DPTR, A
        
        ; 准备下一位
        MOV A, R2
        RL A
        MOV R2, A
        INC R0
        CJNE R0, #36H, DISP_NEXT
        RET

;====================================================================
; 子程序: 完整键盘扫描 (返回 A=0-9, FF=无键)
; 适配图2.1电路: 位选口输出扫描低电平，行读入口读回
;====================================================================
KEY_SCAN_FULL:
        ; --- 列0扫描 (对应键 0, 4, 8, C) ---
        MOV DPTR, #COM8255_BIT
        MOV A, #0FEH       ; 1111 1110 (选通第1列)
        MOVX @DPTR, A
        
        MOV DPTR, #KEY_IN_PORT
        MOVX A, @DPTR      ; 读行
        CPL A              ; 取反，便于判断
        ANL A, #0FH        ; 只看低4位
        JZ SCAN_COL1       ; 此列无键，查下一列
        
        ; 判断行
        JB ACC.0, K_0      ; 行0 -> 键0
        JB ACC.1, K_4      ; 行1 -> 键4
        JB ACC.2, K_8      ; 行2 -> 键8
        SJMP NO_KEY        ; 其他忽略
        
SCAN_COL1:
        ; --- 列1扫描 (对应键 1, 5, 9, D) ---
        MOV DPTR, #COM8255_BIT
        MOV A, #0FDH       ; 1111 1101 (选通第2列)
        MOVX @DPTR, A
        
        MOV DPTR, #KEY_IN_PORT
        MOVX A, @DPTR
        CPL A
        ANL A, #0FH
        JZ SCAN_COL2
        
        JB ACC.0, K_1
        JB ACC.1, K_5
        JB ACC.2, K_9
        SJMP NO_KEY

SCAN_COL2:
        ; --- 列2扫描 (对应键 2, 6, A, E) ---
        MOV DPTR, #COM8255_BIT
        MOV A, #0FBH       ; 1111 1011
        MOVX @DPTR, A
        
        MOV DPTR, #KEY_IN_PORT
        MOVX A, @DPTR
        CPL A
        ANL A, #0FH
        JZ SCAN_COL3
        
        JB ACC.0, K_2
        JB ACC.1, K_6
        SJMP NO_KEY

SCAN_COL3:
        ; --- 列3扫描 (对应键 3, 7, B, F) ---
        MOV DPTR, #COM8255_BIT
        MOV A, #0F7H       ; 1111 0111
        MOVX @DPTR, A
        
        MOV DPTR, #KEY_IN_PORT
        MOVX A, @DPTR
        CPL A
        ANL A, #0FH
        JZ NO_KEY
        
        JB ACC.0, K_3
        JB ACC.1, K_7
        SJMP NO_KEY

NO_KEY:
        MOV A, #0FFH
        RET

; 键值返回 (仅支持0-9数字键，其他忽略或扩展)
K_0: MOV A, #0
     RET
K_1: MOV A, #1
     RET
K_2: MOV A, #2
     RET
K_3: MOV A, #3
     RET
K_4: MOV A, #4
     RET
K_5: MOV A, #5
     RET
K_6: MOV A, #6
     RET
K_7: MOV A, #7
     RET
K_8: MOV A, #8
     RET
K_9: MOV A, #9
     RET

;====================================================================
; 子程序: 等待按键释放
;====================================================================
KEY_WAIT_REL:
        ACALL DISPLAY_SCAN    ; 保持显示
        ACALL KEY_SCAN_FULL   ; 再次扫描
        CJNE A, #0FFH, KEY_WAIT_REL ; 如果仍有键，继续等
        RET

;====================================================================
; 延时子程序
;====================================================================
DELAY_SMALL:
        MOV R7, #30
        DJNZ R7, $
        RET

;====================================================================
; 字形码表 (0-9 及 黑屏)
;====================================================================
SEG_TAB:
        DB 3FH, 06H, 5BH, 4FH, 66H ; 0-4
        DB 6DH, 7DH, 07H, 7FH, 6FH ; 5-9
        DB 00H                     ; 10 (Off)

        END