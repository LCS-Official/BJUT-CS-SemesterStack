.data
a: .space 48  
b: .word 10,11,12,13,1,1 
c: .word 1,2,3,4,5,6 

.text
daddi r1,r0,a     
daddi r2,r0,b     
daddi r3,r0,c     
daddi r4,r0,6   

Loop: 
    ld r5,0(r1)
    ld r6,0(r2)   
    ld r7,0(r3)      
    
    dadd r8,r5,r6   
    dadd r9,r8,r7     
    
    sd r9,0(r1)     
    
    daddi r1,r1,8   
    daddi r2,r2,8  
    daddi r3,r3,8    
    daddi r4,r4,-1   
    bnez r4,Loop     

end: halt