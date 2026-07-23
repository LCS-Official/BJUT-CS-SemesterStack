.data
; Array with 16 elements
arr:    .word 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32
const:  .word 5          ; Constant value to add

.text
main:
    daddi r1, r0, arr    ; r1 = Base address of array
    ld r2, const(r0)     ; r2 = Constant value (5)

    ; PHASE 1: LOAD ALL (Memory Read)

    ld r4,  0(r1)
    ld r5,  8(r1)
    ld r6,  16(r1)
    ld r7,  24(r1)
    ld r8,  32(r1)
    ld r9,  40(r1)
    ld r10, 48(r1)
    ld r11, 56(r1)
    ld r12, 64(r1)
    ld r13, 72(r1)
    ld r14, 80(r1)
    ld r15, 88(r1)
    ld r16, 96(r1)
    ld r17, 104(r1)
    ld r18, 112(r1)
    ld r19, 120(r1)


    ; PHASE 2: CALCULATE ALL (ALU Operation)
    dadd r4,  r4,  r2
    dadd r5,  r5,  r2
    dadd r6,  r6,  r2
    dadd r7,  r7,  r2
    dadd r8,  r8,  r2
    dadd r9,  r9,  r2
    dadd r10, r10, r2
    dadd r11, r11, r2
    dadd r12, r12, r2
    dadd r13, r13, r2
    dadd r14, r14, r2
    dadd r15, r15, r2
    dadd r16, r16, r2
    dadd r17, r17, r2
    dadd r18, r18, r2
    dadd r19, r19, r2

    ; PHASE 3: STORE ALL (Memory Write)
    sd r4,  0(r1)
    sd r5,  8(r1)
    sd r6,  16(r1)
    sd r7,  24(r1)
    sd r8,  32(r1)
    sd r9,  40(r1)
    sd r10, 48(r1)
    sd r11, 56(r1)
    sd r12, 64(r1)
    sd r13, 72(r1)
    sd r14, 80(r1)
    sd r15, 88(r1)
    sd r16, 96(r1)
    sd r17, 104(r1)
    sd r18, 112(r1)
    sd r19, 120(r1)

    halt