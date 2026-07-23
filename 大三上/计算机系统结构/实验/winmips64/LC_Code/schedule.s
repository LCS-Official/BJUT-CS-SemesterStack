.data
val_x:  .word 100        ; Test data X
val_y:  .word 50         ; Test data Y
res_a:  .word 0          ; Result A
res_b:  .word 0          ; Result B

.text
main:


    ; PART 1: Data Hazard (RAW)

    ld r10, val_x(r0)    ; Load X
    dadd r11, r10, r10   ; RAW Stall: Waits for r10 from memory
    sd r11, res_a(r0)    ; RAW Stall: Waits for r11 from EX stage
    

    ; PART 2: Structural Hazard (+ Data Hazard)

    ld r12, val_y(r0)    ; Load Y
    
    ; Instruction 1 using Multiplier
    dmul r13, r12, r12   ; RAW Stall (waits for r12) 
                         ; AND occupies the Multiplier Unit for multiple cycles
    
    ; Instruction 2 using Multiplier
    ; This creates a STRUCTURAL HAZARD because the Multiplier Unit 
    ; is still busy processing the previous instruction.
    dmul r14, r12, r12   ; Structural Stall: Waits for Multiplier Unit to be free
    
    sd r13, res_b(r0)    ; Store Result
    halt