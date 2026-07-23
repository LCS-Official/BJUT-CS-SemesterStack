    ORG 0000H
    LJMP START

START:
    ; 初始化寄存器
    MOV R0, #00H      ; R0作为查表偏移量
    MOV R2, #20H      ; R2作为位选码
SCAN_LOOP:

    MOV DPTR, #DISPLAY_CODES
    MOV A, R0
    MOVC A, @A+DPTR

    MOV DPTR, #8004H
    MOVX @DPTR, A

    MOV DPTR, #8002H
    MOV A, R2
    MOVX @DPTR, A

    ACALL DELAY


    INC R0
    MOV A, R2
    RR A
    MOV R2, A


    CJNE R0, #06H, SCAN_LOOP

    SJMP START

DELAY:
    MOV R7, #10
D1: MOV R6, #50
D2: DJNZ R6, D2
    DJNZ R7, D1
    RET

DISPLAY_CODES:
    DB 06H    ; 显示 '1' 
    DB 3FH    ; 显示 '0' 
    DB 3FH    ; 显示 '0' 
    DB 6DH    ; 显示 '5' 
    DB 3FH    ; 显示 '0' 
    DB 7DH    ; 显示 '6' 

    END
