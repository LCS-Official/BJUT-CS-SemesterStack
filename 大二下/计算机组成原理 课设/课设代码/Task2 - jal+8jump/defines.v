/*
 * --------------------------------------------------------------------
 * 文件名称: defines.v
 * 描述:     存放项目中所有模块会用到的宏定义 (为多周期更新)
 * --------------------------------------------------------------------
 */

// --- 指令 Opcode 定义 (与单周期相同) ---
`define OP_R_TYPE  6'b000000
`define OP_J       6'b000010
`define OP_JAL     6'b000011
`define OP_BEQ     6'b000100
`define OP_ADDI    6'b001000
`define OP_ADDIU   6'b001001
`define OP_ORI     6'b001101
`define OP_LUI     6'b001111
`define OP_LW      6'b100011
`define OP_SW      6'b101011

// --- R-Type 指令 Funct 定义 (与单周期相同) ---
`define FUNCT_ADDU  6'b100001
`define FUNCT_SUBU  6'b100011
`define FUNCT_JR    6'b001000
`define FUNCT_SLT   6'b101010
`define FUNCT_SLL   6'h00

// --- ALU 操作码定义 (与单周期相同) ---
`define ALU_ADD   4'b0000 // 加法
`define ALU_SUB   4'b0001 // 减法
`define ALU_OR    4'b0010 // 或
`define ALU_SLT   4'b0011 // 小于则置1 (有符号)
`define ALU_ADDI  4'b0100 // 带溢出检测的加法
`define ALU_SLL   4'b0101 // 逻辑左移

// --- PC源选择信号 (PCSrc) 定义 ---
`define PC_SRC_ALU      2'b00 // 来源为 ALU 计算结果 (用于PC+4)
`define PC_SRC_BRANCH   2'b01 // 来源为 分支目标地址 (beq)
`define PC_SRC_JUMP     2'b10 // 来源为 跳转目标地址 (j, jal)
`define PC_SRC_JR       2'b11 // 来源为 寄存器跳转地址 (jr)

// --- FSM 状态定义 (为多周期新增) ---
`define S_FETCH        4'b0000 // 状态0: 取指
`define S_DECODE       4'b0001 // 状态1: 译码/读寄存器
`define S_MEM_ADDR_CALC 4'b0010 // 状态2: 计算访存地址 (lw/sw)
`define S_EXECUTE_R    4'b0011 // 状态3: R-type指令执行
`define S_EXECUTE_I    4'b0100 // 状态4: I-type算术/逻辑指令执行
`define S_BRANCH_COMP  4'b0101 // 状态5: 分支指令完成
`define S_MEM_READ     4'b0110 // 状态6: 读内存 (lw)
`define S_MEM_WRITE    4'b0111 // 状态7: 写内存 (sw)
`define S_WB_FROM_MEM  4'b1000 // 状态8: 从内存写回 (lw)
`define S_WB_FROM_ALU_R 4'b1001 // 状态9: R-type写回
`define S_WB_FROM_ALU_I 4'b1010 // 状态10: I-type写回
`define S_JUMP_COMP    4'b1011 // 状态11: 跳转指令完成
`define S_JAL_WB       4'b1100 // 状态12: JAL写回
`define S_JR_COMP       4'b1101 // 状态13: JR指令完成