ORG 0000H
    LJMP START
    ORG 000BH         ; Timer 0 Interrupt Vector
    LJMP TIME_ISR

START:
    MOV SP, #60H      ; Initialize Stack Pointer
    
    ; Initialize Time Variables (HH:MM:SS)
    ; 40H,41H = Hour; 42H,43H = Minute; 44H,45H = Second
    MOV 40H, #1        
    MOV 41H, #2        
    MOV 42H, #0        
    MOV 43H, #0        
    MOV 44H, #0        
    MOV 45H, #0        

    ; Initialize Timer 0
    MOV TMOD, #01H    ; Mode 1 (16-bit)
    MOV TH0, #3CH     ; High byte for 50ms (12MHz)
    MOV TL0, #0B0H    ; Low byte for 50ms
    MOV R7, #20       ; Counter for 1 second (20 * 50ms)
    SETB EA           ; Enable Global Interrupts
    SETB ET0          ; Enable Timer 0 Interrupt
    SETB TR0          ; Start Timer 0

MAIN_LOOP:
    ACALL TIME_TO_BUFFER ; Convert time vars to segment codes
    ACALL DISPLAY_SCAN   ; Scan display once
    SJMP MAIN_LOOP       ; Repeat

; --- Interrupt Service Routine ---
TIME_ISR:
    PUSH ACC          ; Save context
    PUSH PSW
    
    ; Reload Timer
    MOV TH0, #3CH
    MOV TL0, #0B0H
    
    DJNZ R7, EXIT_ISR ; Check if 1 second passed
    MOV R7, #20       ; Reset 1s counter
    
    ; Increment Seconds (Unit)
    INC 45H
    MOV A, 45H
    CJNE A, #10, EXIT_ISR
    MOV 45H, #0
    
    ; Increment Seconds (Ten)
    INC 44H
    MOV A, 44H
    CJNE A, #6, EXIT_ISR
    MOV 44H, #0
    
    ; Increment Minutes (Unit)
    INC 43H
    MOV A, 43H
    CJNE A, #10, EXIT_ISR
    MOV 43H, #0
    
    ; Increment Minutes (Ten)
    INC 42H
    MOV A, 42H
    CJNE A, #6, EXIT_ISR
    MOV 42H, #0
    
    ; Increment Hours Logic
    INC 41H
    MOV A, 41H
    CJNE A, #10, CHECK_24
    ; If Hour Unit is 10, carry to Hour Ten
    MOV 41H, #0
    INC 40H
    SJMP EXIT_ISR

CHECK_24:
    ; Check if time is 24:00:00
    MOV A, 40H
    CJNE A, #2, EXIT_ISR ; If Hour Ten != 2, no reset
    MOV A, 41H
    CJNE A, #4, EXIT_ISR ; If Hour Unit != 4, no reset
    
    ; Reset Day
    MOV 40H, #0
    MOV 41H, #0
    
EXIT_ISR:
    POP PSW           ; Restore context
    POP ACC
    RETI

; --- Convert Time to Display Buffer ---
TIME_TO_BUFFER:
    MOV R0, #40H      ; Source: Time variables
    MOV R1, #30H      ; Dest: Display buffer
    MOV R5, #6        ; Count: 6 digits
CONVERT_LOOP:
    MOV A, @R0
    MOV DPTR, #SEG_TABLE
    MOVC A, @A+DPTR   ; Get segment code
    MOV @R1, A        ; Store in buffer
    INC R0
    INC R1
    DJNZ R5, CONVERT_LOOP
    RET

; --- Display Scanning Routine ---
DISPLAY_SCAN:
    MOV R0, #30H      ; Buffer Start
    MOV R2, #20H      ; Bit Mask Start
SCAN_NEXT:
    ; Blanking
    MOV DPTR, #8002H
    MOV A, #00H
    MOVX @DPTR, A

    ; Output Segment
    MOV A, @R0
    MOV DPTR, #8004H
    MOVX @DPTR, A

    ; Output Bit Select
    MOV DPTR, #8002H
    MOV A, R2
    MOVX @DPTR, A

    ACALL DELAY_SHORT
    
    INC R0
    MOV A, R2
    RR A
    MOV R2, A
    CJNE R0, #36H, SCAN_NEXT
    RET

DELAY_SHORT:
    MOV R6, #50
D_S: DJNZ R6, D_S
    RET

SEG_TABLE:
    DB 3FH, 06H, 5BH, 4FH, 66H
    DB 6DH, 7DH, 07H, 7FH, 6FH

    END