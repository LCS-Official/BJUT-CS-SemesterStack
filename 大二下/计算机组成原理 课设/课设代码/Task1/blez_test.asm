addi $1, $0, -10
addi $2, $0, 10
blez $1, start
ori $16, $0, 1
ori $17, $0, 3
ori $8, $0, 1
ori $12, $0,0xabab
lui $13, 10
start:addu $4, $0,$16
addu $5, $0,$8
blez $2, start2
addu $16, $0, $2
subu $17,$17,$8
beq $16, $17, start
ori $8, $0,4
addiu $24,$0,0x7fffffff
addiu $9,$24,3
addiu $10,$24,5
addi $22,$24,6
start2:sw $9, 0($8)
lw $14, 0($8)
sw $10,4($8)
lw $15,4($8)
sw $4, -4($8)
lw $18, -4($8)
addu $4,$0,$8
addu $5,$0,$9