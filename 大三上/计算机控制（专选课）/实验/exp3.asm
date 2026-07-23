; LED displays hexadecimal numbers
ORG 0000H    ; Program stored starting from ROM address 0000H
OUTBIG EQU 8002H  ; Bit selection signal control address
OUTSEG EQU 8004H  ; Segment selection signal control address
KEYIN  EQU 8001H  ; Keyboard row selection signal control address
DAC    EQU 9000H  ; DAC digital value location, DAC strobe signal is CS1
AJMP INIT  ; Initialize
ORG 000BH   ; T0 interrupt service routine address TIME
AJMP TIME


; T1 counts, T0 times 
INIT:
	MOV SP,  #60H   ; Set Stack Pointer

; Set initial LED display values
	MOV 20H, #06H   ; 1
	MOV 21H, #5bH   ; 2
        MOV 22H, #4fH   ; 3
        MOV 23H, #66H   ; 4
        MOV 24H, #6dH   ; 5
	MOV 25H, #7dH   ; 6

	MOV 26H, #00H   ; Used to store expected value
	MOV 27H, #00H   ; Used to record interrupt count
	MOV 28H, #01H   ; Record low byte of expected value
       MOV 29H, #20H   ; 

	MOV TMOD, #51H  ; (0101_0001)B, T1 works in Mode 1, T0 works in Mode 1
	MOV TL0, #0CEH  ; 
	MOV TH0, #00H   ; Set T0 timing constant to 206. If crystal is 12MHz, then every 20 interrupts is 1 second?
	MOV TL1, #00H
	MOV TH1, #00H   ; Set initial T1 counter value to 0
	SETB ET0        ; Enable T0 interrupt
	SETB EA         ; Enable global interrupts
	SETB TR0        ; Start timer
	SETB TR1        ; Start counter


MAIN:
	LCALL DACHANGE  ; D/A Conversion
	LCALL DISPLAY   ; No key input, continue displaying current number (Hex)
	LCALL TEST      ; Test if there is keyboard input
	JZ MAIN         ; Accumulator is 0, no key press, continue displaying
	LCALL SEARCH    ; Key input detected, get key value, store in A
	MOV 20H, 21H    ; Left 2 digits of 7-segment display shift left

	MOV B, 28H      ; High byte of expected value stored in B
	MOV 28H, A      ; Record low byte of expected value

	MOV DPTR, #LEDTAB
	MOVC A, @A + DPTR  ; Convert key value to segment code
	MOV 21H, A         ; Put new key value's segment code into the 2nd LED from left

	MOV A, #10H  ; Put multiplier 16 into A
	MUL AB       ; High byte in B, low byte in A
	ADD A, 28H   ; Result of expected value in A
	MOV 26H, A   ; Store expected value in 26H

	LCALL DACHANGE  ; D/A Conversion
	SJMP MAIN


; D/A Conversion
DACHANGE:
	MOV DPTR, #DAC
	MOV A, 29H
	MOVX @DPTR, A
	RET


; Display Module
DISPLAY:
	MOV R0, #20H  ; Buffer starts at 20H
	MOV R1, #6    ; Total 6 seven-segment displays
	MOV R2, #00100000B   ; Start display from left, 1 is on, 0 is off

LOOP:      
	MOV DPTR, #OUTSEG
	MOV A, #0
	MOVX @DPTR, A  ; Set segment code to 0
	MOV A, @R0     ; Send memory value starting at 20H to segment output port 8004H
	MOVX @DPTR, A

	MOV DPTR, #OUTBIG
	MOV A, R2
	MOVX @DPTR, A  ; Output bit selection signal, enable one 7-segment display at a time
	RR A
	MOV R2, A
	LCALL DELAY    ; Delay
	INC R0
	DJNZ R1, LOOP  ; Display 6 times

	RET


; Delay Subroutine
DELAY:
	MOV R7, #02H
DEL1:    
	MOV R6, #0ffH
DEL2:    
	DJNZ R6, DEL2
	DJNZ R7, DEL1
	RET


; Detect if there is keyboard input
TEST:
	MOV DPTR, #OUTBIG
	MOV A, #00H
	MOVX @DPTR, A
	MOV DPTR, #KEYIN
	MOVX A, @DPTR  ; Read back row status
	CPL A          ; Complement bits in Accumulator A
	ANL A, #0FH    ; Take low 4 bits of A
	RET


; Get pressed key information
SEARCH:
	MOV R1, #00100000B  ; Initial column, start from the left
	MOV R2, #06H        ; Search 6 columns
	MOV R5, #00H        ; Record current column
	MOV R4, #03H        ; Number of columns already skipped

; Find valid column and row
LSEARCH:
	MOV A, R1
	CPL A    ; Keyboard column scan active low, LED bit select active high
	MOV DPTR, #OUTBIG
	MOVX @DPTR, A
	CPL A
	RR A     ; Always rotate LED bit select signal right, store in R1
	MOV R1, A
	MOV DPTR, #KEYIN
	MOVX A, @DPTR  ; Read keyboard row scan signal (active low)
	CPL A
	ANL A, #0FH    ; Take low 4 bits
	JNZ HSEARCH    ; If A is not zero, column and row found (Col in R1, Row in A)
	INC R5         ; If A is all zero, increment column count and continue search
	DJNZ R2, LSEARCH  ; At least 6 iterations to find

; Convert row from binary bit representation to index form
HSEARCH:
	MOV R7, #04H    ; Total 4 rows
LOOP2:    
	RRC A
	JC GET
	DEC R4
	DJNZ R7, LOOP2

; Determine input key code value
GET:
	MOV A, R4    ; Key offset on keyboard = Row * 6 + Col, R4 * 6 + R5 -> A
	MOV B, #6H
	MUL AB
	ADD A, R5
	MOV DPTR, #KEYTAB
	MOVC A, @A + DPTR
	MOV 26H, A   ; Temporarily save key value in memory to prevent data loss

WAIT:   
	MOV DPTR, #OUTBIG    ; Wait for key release
	CLR A
	MOVX @DPTR, A
	LCALL DELAY
	LCALL TEST
	JNZ WAIT
	MOV A, 26H    ; Store key value into A
	RET


; T0 Interrupt Service Routine TIME
TIME:
	PUSH PSW
	PUSH ACC
	PUSH B
	PUSH DPL
	PUSH DPH
	SETB RS0     ; Select Register Bank 1
	CLR  RS1
	MOV R0, 27H  ; Retrieve interrupt count
	INC R0       ; Increment interrupt count
	MOV 27H,R0   ; Store back interrupt count
	CJNE R0, #25H, END1   ; If not 20, return directly
	MOV R0, #00H
	MOV 27H, R0  ; Store back interrupt count
	CLR TR0      ; Stop timer
	CLR TR1      ; Stop counter
	MOV 30H, TL1 ; Send counter low byte to 30H
	MOV 31H, TH1 ; Send counter high byte to 31H
	MOV A, 30H   ; Dividend in A
	MOV B, #10H  ; Divisor in B
	DIV AB       ; Result: Quotient in A, Remainder in B
	MOV DPTR, #LEDTAB
	MOVC A, @A + DPTR  ; Convert key value to segment code
	MOV 24H, A
	MOV A, B
	MOVC A, @A + DPTR  ; Convert key value to segment code
	MOV 25H, A

	MOV A, 31H    ; Dividend in A
	MOV B, #10H   ; Divisor in B
	DIV AB        ; Result: Quotient in A, Remainder in B
	MOV DPTR, #LEDTAB
	MOVC A, @A + DPTR  ; Convert key value to segment code
	MOV 22H, A
	MOV A, B
	MOVC A, @A + DPTR  ; Convert key value to segment code
	MOV 23H, A

	MOV A, 31H      ; Get high byte of speed
	JNZ SPEEDDOWN   ; High byte not 0, speed too fast, slow down
	MOV A, 30H      ; Get low byte of speed
	CLR CY          ; Clear CY flag
	SUBB A, 26H     ; Subtract expected value from speed, result in A
	JB CY, SPEEDUP  ; Borrow occurred, speed too low, speed up
	JZ SUBEND       ; If A is zero, speed matches expected value, jump
	SJMP SPEEDDOWN  ; Otherwise speed too fast, slow down

SPEEDDOWN:
	MOV A, 29H     ; Put digital value into A
	ADDC A, #01H   ; Increment digital value
	MOV 29H, A
	SJMP SUBEND

SPEEDUP:
	MOV A, 29H     ; Put digital value into A
	SUBB A, #01H   ; Decrement digital value
	MOV 29H, A
	SJMP SUBEND

; Re-initialize and start timing/counting
SUBEND:
	MOV TL0, #0CEH
	MOV TH0, #00H   ; Set T0 timing constant to 206. If crystal is 12MHz, then every 20 interrupts is 1 second?
	MOV TL1, #00H
	MOV TH1, #00H   ; Set initial T1 counter value to 0
	SETB ET0        ; Enable T0 interrupt
	SETB EA         ; Enable global interrupts
	SETB TR0        ; Start timer
	SETB TR1        ; Start counter
END1:	
	POP DPH
	POP DPL
	POP B
	POP ACC
	POP PSW
	RETI     ; Interrupt return


; Segment Codes and Values
; 7-segment display codes
LEDTAB:
	DB 3fh, 06h, 5bh, 4fh, 66h, 6dh, 7dh, 07h
	DB 7fh, 6fh, 77h, 7ch, 39h, 5eh, 79h, 71h

; Keyboard codes
KEYTAB:
	DB 07h, 08h, 09h, 0ah, 10h, 0ffh
	DB 04h, 05h, 06h, 0bh, 11h, 14h
	DB 01h, 02h, 03h, 0ch, 12h, 15h
	DB 00h, 0fh,0eh, 0dh, 13h, 16h