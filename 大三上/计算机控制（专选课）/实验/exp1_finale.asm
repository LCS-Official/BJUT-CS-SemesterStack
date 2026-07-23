OUTBIG EQU 8002H
OUTSEG EQU 8004H
KEYIN  EQU 8001H

READY:
          MOV 25H,#06H
          MOV 24H,#00H
          MOV 23H,#05H
          MOV 22H,#00H
          MOV 21H,#00H
          MOV 20H,#01H

          MOV R7,#6
MAIN:
          LCALL DISPLAY
          LCALL TEST
          JZ MAIN
          LCALL SEARCH
          MOV 20H,21H
          MOV 21H,22H
          MOV 22H,23H
          MOV 23H,24H
          MOV 24H,25H
          MOV 25H,A
          DJNZ R7, MAIN

SHIZHONG:
          LCALL DELONE
          LCALL ADD1
          SJMP SHIZHONG

DISPLAY:
          MOV R0,#20H
          MOV R1,#6
          MOV R2,#00100000B

LOOP3:
          MOV DPTR,#LEDTAB
          MOV A,@R0
          MOVC A,@A+DPTR
          MOV B,A

          MOV DPTR,#OUTSEG
          MOV A,#0
          MOVX @DPTR,A
          MOV A,B
          MOVX @DPTR,A

          MOV DPTR,#OUTBIG
          MOV A,R2
          MOVX @DPTR,A
          RR A
          MOV R2,A
          LCALL DELAY
          INC R0
          DJNZ R1,LOOP3
          RET

DELAY:
          MOV R5,#01H
DEL1:     MOV R6,#00H
DEL2:     DJNZ R6,DEL2
          DJNZ R5,DEL1
          RET

TEST:
          MOV DPTR,#OUTBIG
          MOV A,#00H
          MOVX @DPTR,A
          MOV DPTR,#KEYIN
          MOVX A,@DPTR
          CPL  A
          ANL A,#0FH
          RET

SEARCH:
          MOV R1,#00100000B
          MOV R2,#06H
          MOV R5,#00H
          MOV R4,#03H
LSEARCH:
          MOV A,R1
          CPL A
          MOV DPTR,#OUTBIG
          MOVX @DPTR,A
          CPL A
          RR A
          MOV R1,A
          MOV DPTR,#KEYIN
          MOVX A,@DPTR
          CPL A
          ANL A,#0FH
          JNZ HSEARCH
          INC R5
          DJNZ R2,LSEARCH
HSEARCH:
          MOV R6,#04H
LOOP2:    RRC A
          JC GET
          DEC R4
          DJNZ R6,LOOP2
GET:
          MOV A,R4
          MOV B,#6H
          MUL AB
          ADD A,R5
          MOV DPTR,#KEYTAB
          MOVC A,@A+DPTR
          MOV 26H,A
WAIT:
          MOV DPTR,#OUTBIG
          CLR A
          MOVX @DPTR,A
          LCALL DELAY
          LCALL TEST
          JNZ WAIT
          MOV A,26H
          RET

ADD1:
          MOV A,25H
          INC A
          MOV 25H,A
          CJNE A,#0AH,QUIT
          MOV 25H,#00H
          MOV A,24H
          INC A
          MOV 24H,A
          CJNE A,#06H,QUIT
          MOV 24H,#00H
          MOV A,23H
          INC A
          MOV 23H,A
          CJNE A,#0AH,QUIT
          MOV 23H,#00H
          MOV A,22H
          INC A
          MOV 22H,A
          CJNE A,#06H,QUIT
          MOV 22H,#00H
          MOV A,20H
          CJNE A,#02H,HOUR019
          JMP HOUR2024
HOUR019:
          MOV A,21H
          INC A
          MOV 21H,A
          CJNE A,#0AH,QUIT
          MOV 21H,#00H
          MOV A,20H
          INC A
          MOV 20H,A
          JMP QUIT
HOUR2024:
          MOV A,21H
          INC A
          MOV 21H,A
          CJNE A,#04H,QUIT
          MOV 21H,#00H
          MOV 20H,#00H
          JMP QUIT
QUIT:
          RET

DELONE:
          MOV 27H,#3
L3:       MOV 28H,#10
L2:       MOV 29H,#10
L1:       LCALL DISPLAY
          DJNZ 29H,L1
          DJNZ 28H,L2
          DJNZ 27H,L3
          RET

LEDTAB:
          DB 3fh, 06h, 5bh, 4fh, 66h, 6dh, 7dh, 07h
          DB 7fh, 6fh, 77H, 7CH, 39H, 5EH, 79H, 71H
KEYTAB:
          DB 07h, 08h, 09h, 0ah, 10h, 0ffh
          DB 04h, 05h, 06h, 0bh, 11h, 14h
          DB 01h, 02h, 03h, 0ch, 12h, 15h
          DB 00h, 0fh,0eh, 0dh, 13h, 16h