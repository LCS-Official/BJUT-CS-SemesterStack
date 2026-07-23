.data
X: .word 20 
Y: .word 5     
Z: .word 0      
.text
main:
ld r1,X(r0)      
ld r2,Y(r0)  
dadd r6,r1,r2  
sd r6,Z(r0)
halt