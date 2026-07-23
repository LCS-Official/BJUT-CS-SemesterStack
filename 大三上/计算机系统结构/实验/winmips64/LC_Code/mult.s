.data
A:      .word 10 
B:      .word 20    
Result: .word 0         

.text
main:
    ld r4, A(r0)     
    ld r5, B(r0)     
    dmul r3, r4, r5    
    sd r3, Result(r0) 
    halt       