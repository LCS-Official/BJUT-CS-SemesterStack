start_loop:
    lw $t7, 0($a0)
    lw $s0, 0($a1)
    beq $s0, $t7, branch_target
    sw $t7, 0($a1)
    sw $t7, 0($a2)
    j start_loop

branch_target:
    lw $s0, 0($a2)
    addiu $s0, $s0, 1
    sw $s0, 0($a2)
    ori $t5, $zero, 10
    sw $t5, 0($v0)
    eret