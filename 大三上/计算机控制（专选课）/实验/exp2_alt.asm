;====================================================================
; 实验名称：步进电机控制 (加速-匀速-减速)
; 硬件连接：P1.0 - P1.3 接 步进电机驱动端 A, B, C, D
;====================================================================

;--- 定义变量 ---
DELAY_VAL   EQU 30H      ; 存储当前延时常数 (控制速度)
STEP_IDX    EQU 31H      ; 当前步进索引 (0-3)

;--- 定义常量 ---
START_SPEED EQU 150      ; 起始速度延时值 (数值越大越慢)
MAX_SPEED   EQU 50       ; 最大速度延时值 (数值越小越快)
                         ; 注意：加速时延时值减小 (150 -> 50)
                         ; 减速时延时值增加 (50 -> 150)

        ORG 0000H
        LJMP START

        ORG 0030H
START:
        MOV P1, #00H     ; 初始化P1口
        MOV STEP_IDX, #0 ; 初始化步序索引

MAIN_LOOP:
        ;========================================
        ; 第一阶段：正转 (CW)
        ;========================================
        
        ; 1. 正转加速 100步
        MOV R5, #START_SPEED    ; 设定初始速度(慢)
        MOV R7, #100            ; 循环100次
CW_ACCEL:
        ACALL STEP_CW           ; 输出一步(正转)
        ACALL DELAY_VAR         ; 可变延时
        DEC R5                  ; 延时减小 -> 速度增加
        DJNZ R7, CW_ACCEL

        ; 2. 正转匀速 100步
        ; R5 保持在上次加速结束后的值(约50)
        MOV R7, #100
CW_CONST:
        ACALL STEP_CW
        ACALL DELAY_VAR
        DJNZ R7, CW_CONST

        ; 3. 正转减速 100步
        MOV R7, #100
CW_DECEL:
        ACALL STEP_CW
        ACALL DELAY_VAR
        INC R5                  ; 延时增加 -> 速度减慢
        DJNZ R7, CW_DECEL

        ACALL DELAY_STOP        ; 停顿一下，保护电机

        ;========================================
        ; 第二阶段：反转 (CCW)
        ;========================================
        
        ; 1. 反转加速 100步
        MOV R5, #START_SPEED    ; 重置为初始慢速
        MOV R7, #100
CCW_ACCEL:
        ACALL STEP_CCW          ; 输出一步(反转)
        ACALL DELAY_VAR
        DEC R5
        DJNZ R7, CCW_ACCEL

        ; 2. 反转匀速 100步
        MOV R7, #100
CCW_CONST:
        ACALL STEP_CCW
        ACALL DELAY_VAR
        DJNZ R7, CCW_CONST

        ; 3. 反转减速 100步
        MOV R7, #100
CCW_DECEL:
        ACALL STEP_CCW
        ACALL DELAY_VAR
        INC R5
        DJNZ R7, CCW_DECEL
        
        ACALL DELAY_STOP        ; 停顿一下

        SJMP MAIN_LOOP          ; 无限循环

;====================================================================
; 子程序：正转输出一步 (STEP_CW)
; 逻辑：索引 +1，查表输出
;====================================================================
STEP_CW:
        PUSH ACC
        PUSH DPH
        PUSH DPL
        
        MOV A, STEP_IDX
        INC A                   ; 索引加1
        ANL A, #03H             ; 保证在 0-3 之间 (模4)
        MOV STEP_IDX, A         ; 更新索引
        
        MOVC A, @A+DPTR         ; 查表 (DPTR需指向表头，下面设置)
                                ; 修正：DPTR在每次调用前未设置，需在此处设置
        MOV DPTR, #STEP_TAB
        MOVC A, @A+DPTR
        
        MOV P1, A               ; 输出到电机
        
        POP DPL
        POP DPH
        POP ACC
        RET

;====================================================================
; 子程序：反转输出一步 (STEP_CCW)
; 逻辑：索引 -1，查表输出
;====================================================================
STEP_CCW:
        PUSH ACC
        PUSH DPH
        PUSH DPL
        
        MOV A, STEP_IDX
        DEC A                   ; 索引减1
        ANL A, #03H             ; 保证在 0-3 之间 (0xFF & 03H = 3)
        MOV STEP_IDX, A
        
        MOV DPTR, #STEP_TAB
        MOVC A, @A+DPTR
        MOV P1, A
        
        POP DPL
        POP DPH
        POP ACC
        RET

;====================================================================
; 子程序：可变延时 (DELAY_VAR)
; 输入参数：R5 (控制延时长度)
;====================================================================
DELAY_VAR:
        PUSH R6
        PUSH R5             ; 保护R5，因为里面存着当前速度值
        
D_LOOP1:
        MOV R6, #100        ; 内层循环常数
D_LOOP2:
        DJNZ R6, D_LOOP2
        DJNZ R5, D_LOOP1    ; 外层由 R5 控制
        
        POP R5
        POP R6
        RET

;====================================================================
; 子程序：停止间隙延时 (防止正反转瞬间电流过大)
;====================================================================
DELAY_STOP:
        MOV R5, #200        ; 长延时
        ACALL DELAY_VAR
        ACALL DELAY_VAR
        RET

;====================================================================
; 数据表：四相单4拍 (A->B->C->D)
; P1.0=A, P1.1=B, P1.2=C, P1.3=D
;====================================================================
STEP_TAB:
        DB 01H  ; 0001 (A相)
        DB 02H  ; 0010 (B相)
        DB 04H  ; 0100 (C相)
        DB 08H  ; 1000 (D相)

        END