start:
    ori $at, $zero, 0x7f00
    ori $v0, $zero, 0x7f04
    ori $v1, $zero, 0x7f08
    ori $a0, $zero, 0x7f0c
    ori $a1, $zero, 0x7f10
    ori $a2, $zero, 0x7f14
    lw $t7, 0($a0)
    sw $t7, 0($a1)
    sw $t7, 0($a2)
    ori $t4, $zero, 0x401
    mtc0 $t8, $12
    mfc0 $t2, $15
    ori $t5, $zero, 10
    ori $t1, $zero, 9
    sw $t5, 0($v0)
    sw $t5, 0($v1)
    sw $t1, 0($at)
    j start