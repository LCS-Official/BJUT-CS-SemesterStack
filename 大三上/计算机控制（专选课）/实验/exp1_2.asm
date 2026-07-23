;========================================================
; 实验1：键盘输入及LED显示输出实验
; 子实验2：键盘输入，最后键号显示在最右端，其余左移
; 初始显示： 1 0 0 5 0 6
; 单片机：MCS-51 (8031/32)
; 接线假定：KEY/LED CS -> CS0
;    段码端口：8004H
;    位码端口：8002H
;    键盘行码：8001H
;========================================================

SEG_PORT  EQU 8004H       ; 段码输出口
BIT_PORT  EQU 8002H       ; 位选/列扫描口
KEY_PORT  EQU 8001H       ; 键盘行码输入口

DISP_BUF  EQU 30H         ; 内部RAM 30H~35H，用来存6位显示的“数字值”(0~9)

            ORG 0000H
            SJMP START

;--------------------------------------------------------
; 代码区开始
;--------------------------------------------------------
START:      MOV SP,#2FH          ; 设置堆栈起始地址（避开30H~35H）

            ACALL INIT_BUF       ; 初始化显示缓冲区：100506

MAIN_LOOP:  ACALL DISP_REFRESH   ; 刷新数码管若干次，保证亮度

            ACALL KEY_SCAN       ; 扫描键盘，看是否有新的按键
            JNC  MAIN_LOOP       ; CY=0表示没新键，继续循环

            ; CY=1且 A 中是新按键对应的“数字值”(0~9)
            ACALL SHIFT_INSERT   ; 左移一位，最右端插入新数字

            SJMP MAIN_LOOP

;--------------------------------------------------------
; 初始化显示缓冲区：1 0 0 5 0 6
; DISP_BUF[0] 最左端，DISP_BUF[5] 最右端
;--------------------------------------------------------
INIT_BUF:   MOV R0,#DISP_BUF     ; R0 指向 buf[0]

            MOV A,#1             ; LED5 显示 1
            MOV @R0,A
            INC R0
            MOV A,#0             ; LED4 显示 0
            MOV @R0,A
            INC R0
            MOV @R0,A            ; LED3 显示 0
            INC R0
            MOV A,#5             ; LED2 显示 5
            MOV @R0,A
            INC R0
            MOV A,#0             ; LED1 显示 0
            MOV @R0,A
            INC R0
            MOV A,#6             ; LED0 显示 6
            MOV @R0,A

            RET

;--------------------------------------------------------
; 显示刷新子程序
; 功能：按 DISP_BUF 中的数字值（0~9），
;       利用查表转换为段码，循环扫描6位数码管刷新
;--------------------------------------------------------
DISP_REFRESH:
            MOV R7,#40           ; 外层循环次数，次数越多越亮

REFRESH_LOOP:
            MOV R6,#6            ; 6个数码管
            MOV R5,#0            ; R5 作为位号 0~5

DIG_LOOP:
            ; 1) 输出位选（BIT_TAB[位号]）
            MOV A,R5
            MOV DPTR,#BIT_TAB
            MOVC A,@A+DPTR       ; A = 当前位选码
            MOV DPTR,#BIT_PORT
            MOVX @DPTR,A

            ; 2) 取当前数字 DISP_BUF[位号]
            MOV R0,#DISP_BUF
            MOV A,R5
            ADD A,R0             ; A = DISP_BUF + index
            MOV R0,A
            MOV A,@R0            ; A = 数字(0~9)

            ; 3) 查段码表 DIG_TAB[数字]
            MOV DPTR,#DIG_TAB
            MOVC A,@A+DPTR       ; A = 段码
            MOV DPTR,#SEG_PORT
            MOVX @DPTR,A

            ; 4) 小延时，保证该位有足够显示时间
            ACALL SHORT_DELAY

            ; 下一位
            INC R5
            DJNZ R6,DIG_LOOP

            DJNZ R7,REFRESH_LOOP
            RET

;--------------------------------------------------------
; SHIFT_INSERT
; 功能：A 中带入新按键的数字值(0~9)
;       将原 6 位整体左移一位，最右端插入新数字
;       即 buf[0]=buf[1],..., buf[4]=buf[5], buf[5]=新数字
;--------------------------------------------------------
SHIFT_INSERT:
            MOV R5,A             ; 暂存新数字

            MOV R0,#DISP_BUF
            MOV R1,#5            ; 需要做5次复制：0<-1,1<-2,...,4<-5

SHIFT_LOOP:
            INC R0               ; R0 指向 buf[i+1]
            MOV A,@R0            ; A = buf[i+1]
            DEC R0               ; 回到 buf[i]
            MOV @R0,A            ; buf[i] = buf[i+1]
            INC R0               ; R0++ -> 下一个 i
            DJNZ R1,SHIFT_LOOP   ; 做完5次后，R0 正好指向 buf[5]

            MOV A,R5
            MOV @R0,A            ; buf[5] = 新数字

            RET

;--------------------------------------------------------
; KEY_SCAN
; 功能：扫描 4×6 键盘，若无键按下，则 CY=0 直接返回
;       若有键按下，去抖动并等待松手，
;       最后 CY=1，A 中为对应的“数字值”(0~9)
; 说明：
;   - 列扫描使用与位选相同的一组位码（BIT_TAB）
;   - 行码从 KEY_PORT(8001H) 读入，低4位为行，某位为0表示该行有按键
;   - 按键编码 -> 通过 KEYMAP 表转换成 0~9 的数字（你可按实际键帽修改）
;--------------------------------------------------------
KEY_SCAN:
            ACALL DETECT_KEY     ; 第一次检测
            JNC  NO_NEW_KEY      ; 没键按下

            ACALL DEBOUNCE       ; 去抖动延时

            ACALL DETECT_KEY     ; 再检测一次确认
            JNC  NO_NEW_KEY      ; 如果第二次没有，则认为是抖动

            ; 此时 A 中已经是 KEYMAP 映射后的数字(0~9)
            MOV R5,A             ; 暂存

WAIT_RELEASE:
            ACALL DETECT_KEY
            JC   WAIT_RELEASE    ; 只要还有键按下，就一直等（免得长按重复）

            MOV A,R5
            SETB C               ; CY=1 表示有新键
            RET

NO_NEW_KEY:
            CLR C
            RET

;--------------------------------------------------------
; DETECT_KEY
; 功能：扫描所有6列，若发现某列某行有按键：
;       - 计算按键序号 index = row*6 + col (0~23)
;       - 通过 KEYMAP[index] 映射得到数字值(0~9)
;       - CY=1，A=数字
;     若无按键，则 CY=0 返回
;--------------------------------------------------------
DETECT_KEY:
            CLR C                ; 先默认无键

            MOV R4,#6            ; 扫描 6 列
            MOV R3,#0            ; R3 = 当前列号 0~5

NEXT_COL:
            ; 输出当前列扫描码（与位选相同）
            MOV A,R3
            MOV DPTR,#BIT_TAB
            MOVC A,@A+DPTR       ; A = 当前列的位码
            MOV DPTR,#BIT_PORT
            MOVX @DPTR,A

            ACALL SHORT_DELAY    ; 稍微等一下，保证行信号稳定

            ; 读取行码（低4位）
            MOV DPTR,#KEY_PORT
            MOVX A,@DPTR
            ANL A,#0FH           ; 只保留低 4 位

            CJNE A,#0FH,FOUND_COL ; !=0FH 表示至少有一行被拉低
            ; 该列无键，换下一列
            INC R3
            DJNZ R4,NEXT_COL

            ; 所有列都无键
            CLR C
            RET

FOUND_COL:
            ; 现在 A 为行码，哪一位为 0，对应哪一行
            ; 行0:1110b(0EH)，行1:1101b(0DH)，行2:1011b(0BH)，行3:0111b(07H)

            CJNE A,#0EH,CHK_ROW1
            MOV R2,#0
            SJMP GOT_ROW
CHK_ROW1:   CJNE A,#0DH,CHK_ROW2
            MOV R2,#1
            SJMP GOT_ROW
CHK_ROW2:   CJNE A,#0BH,CHK_ROW3
            MOV R2,#2
            SJMP GOT_ROW
CHK_ROW3:   CJNE A,#07H,NO_VALID
            MOV R2,#3
            SJMP GOT_ROW

NO_VALID:
            CLR C
            RET

GOT_ROW:
            ; 计算 index = row*6 + col
            MOV A,R2
            MOV B,#6
            MUL AB               ; A = row*6
            ADD A,R3             ; A = row*6 + col = index(0~23)

            ; KEYMAP[index] -> 映射到 0~9 的数字值
            MOV DPTR,#KEYMAP
            MOVC A,@A+DPTR       ; A = 数字(0~9)

            SETB C
            RET

;--------------------------------------------------------
; 短延时子程序 SHORT_DELAY
;--------------------------------------------------------
SHORT_DELAY:
            MOV R0,#80
SD_LOOP:    DJNZ R0,SD_LOOP
            RET

;--------------------------------------------------------
; 去抖动延时子程序 DEBOUNCE（时间稍长一点）
;--------------------------------------------------------
DEBOUNCE:
            MOV R1,#200
DB_LOOP:    DJNZ R1,DB_LOOP
            RET

;--------------------------------------------------------
; 数据表：段码表（共阴极） 0~9
;         BIT_TAB：6位数码管的位选码（与例程一致）
;         KEYMAP：按键序号 0~23 --> 显示数字(0~9)
;--------------------------------------------------------
; 数码管字型码表（a,b,c,d,e,f,g）
; 0~9，与你指导书图3.2 中的常用编码一致
DIG_TAB:    DB  3FH    ; 0
            DB  06H    ; 1
            DB  5BH    ; 2
            DB  4FH    ; 3
            DB  66H    ; 4
            DB  6DH    ; 5
            DB  7DH    ; 6
            DB  07H    ; 7
            DB  7FH    ; 8
            DB  6FH    ; 9

; 位选码（6位，从左到右：LED5, LED4, ... , LED0）
; 与学校提供的 LED 显示 8 的例程相同：最左为 20H，然后右移
BIT_TAB:    DB  20H    ; LED5（最左）
            DB  10H
            DB  08H
            DB  04H
            DB  02H
            DB  01H    ; LED0（最右）

; 键盘映射表： index = row*6 + col (0~23) -> 显示的数字(0~9)
; 这里先给一个简单的映射： 0,1,2,3,4,5,6,7,8,9,0,1,...
; 你可以根据实际按键布局(哪一键是“0”“1”……)自己调整
KEYMAP:     DB  0,1,2,3,4,5
            DB  6,7,8,9,0,1
            DB  2,3,4,5,6,7
            DB  8,9,0,1,2,3

            END
