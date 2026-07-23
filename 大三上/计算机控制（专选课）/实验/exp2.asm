STRT:MOV 20H,#00H     ; Set D7 of 20H to 0 for Forward; D1D0 used as address offset
     MOV P1,#01H      ; Stepper motor init, P1=#01H, energize Phase A
     MOV 42H,#0A0H    ; Load 0A0H (160) into delay counter 42H

     acall speedup    ; Call acceleration subroutine
     MOV 20H,#00H     ; Set D7 of 20H to 0 for Forward
     acall speed      ; Call constant speed subroutine
     MOV 20H,#00H     ; Set D7 of 20H to 0 for Forward
     acall speedlow   ; Call deceleration subroutine

     MOV 20H,#80H     ; Set D7 of 20H to 1 for Reverse; D1D0 used as address offset
     MOV P1,#01H      ; Stepper motor init, P1=#01H, energize Phase A
     MOV 42H,#0A0H    ; Load 0A0H (160) into delay counter 42H

     acall speedup    ; Call acceleration subroutine
     MOV 20H,#80H     ; Set D7 of 20H to 1 for Reverse
     acall speed      ; Call constant speed subroutine
     MOV 20H,#80H     ; Set D7 of 20H to 1 for Reverse
     acall speedlow   ; Call deceleration subroutine

     sjmp strt        ; Loop back to start

 ; Acceleration Subroutine
speedup: MOV   R7,#64H     ; Load 100 (64H) into step counter R7
MLP0:    MOV   R6,42H      ; Load delay value
MLPX0:   LCALL DEL         ; Call short delay subroutine
         DJNZ  R6,MLPX0    ; Loop delay
         DEC   42H         ; Decrement delay counter 42H (Decrease delay = Speed up)
         LCALL STEPS       ; Call single step subroutine
         DJNZ  R7,MLP0     ; Decrement step count, continue if not zero
         ret

 ; Constant Speed Subroutine
speed:   MOV   R7,#64H     ; Load 100 (64H) into step counter R7
MLP1:    MOV   R6,42H      ; Load delay value
MLPX1:   LCALL DEL         ; Call short delay subroutine
         DJNZ  R6,MLPX1    ; Loop delay
         LCALL STEPS       ; Call single step subroutine
         DJNZ  R7,MLP1     ; Decrement step count, continue if not zero
         RET

 ; Deceleration Subroutine
speedlow:MOV   R7,#0C8H    ; Load 200 (0C8H) into step counter R7
MLP2:    MOV   R6,42H      ; Load delay value
MLPX2:   LCALL DEL         ; Call short delay subroutine
         DJNZ  R6,MLPX2    ; Loop delay
         Inc   42H         ; Increment delay counter 42H (Increase delay = Speed down)
         LCALL STEPS       ; Call single step subroutine
         DJNZ  R7,MLP2     ; Decrement step count, continue if not zero
         ret

; Single Step Subroutine
STEPS:   INC    20H              ; Increment address offset
         ANL    20H,#83H         ; Keep D7, D1, D0 of 20H; Mask others
         JB     7, STPSC         ; If D7=1 jump to Reverse; if D7=0 Forward
         MOV    DPTR,#FTAB       ; Load Forward Table address to DPTR
         SJMP   STPW             ; Jump to table lookup
STPSC:   MOV    DPTR, #CTAB      ; Load Reverse Table address to DPTR
STPW:    MOV    A,20H            ; Table lookup routine
         ANL    A,#03H           ; Extract address offset (lower 2 bits)
         MOVC   A,@A+DPTR        ; Get phase data from table
         MOV    P1,A             ; Output phase data to P1, motor steps once
         RET

FTAB:DB 01H,02H,04H,08H    ; Forward rotation table
CTAB:DB 01H,08H,04H,02H    ; Reverse rotation table

; Short Delay Subroutine
DEL:   MOV  R5,#40H        ; 1T
DEL0:  DJNZ  R5,DEL0       ; 2T
       RET                 ; 1T
END                        ; End of program