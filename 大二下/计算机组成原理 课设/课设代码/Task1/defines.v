// 文件名称: defines.v
// 描述:     存放项目中所有模块会用到的宏定义

// ALU 操作码定义
`define ALU_ADD   4'b0000 // 加法
`define ALU_SUB   4'b0001 // 减法
`define ALU_OR    4'b0010 // 或
`define ALU_SLT   4'b0011 // 小于则置1 (有符号)
`define ALU_ADDI  4'b0100 // 带溢出检测的加法
`define ALU_SLL   4'b0101 // 逻辑左移

// PC源选择信号 (PCSrc) 定义
`define PC_SRC_P4      2'b00 // 来源为 PC+4
`define PC_SRC_BRANCH  2'b01 // 来源为 分支目标地址 (beq)
`define PC_SRC_JUMP    2'b10 // 来源为 跳转目标地址 (j, jal)
`define PC_SRC_JR      2'b11 // 来源为 寄存器跳转地址 (jr)

// --- 指令 Opcode 定义 ---
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

// --- R-Type 指令 Funct 定义 ---
`define FUNCT_ADDU  6'b100001
`define FUNCT_SUBU  6'b100011
`define FUNCT_JR    6'b001000
`define FUNCT_SLT   6'b101010
`define FUNCT_SLL   6'h00 // sll功能码

// --- GPR写回数据选择信号 (WriteBackSel) 定义 ---
`define WB_ALU  2'b00 // 数据来源为 ALU result
`define WB_MEM  2'b01 // 数据来源为 Data Memory
`define WB_PC4  2'b10 // 数据来源为 PC+4 (用于jal)
`define WB_LUI  2'b11 // 数据来源为 lui的立即数 (imm<<16)

// For blez
`define OP_BLEZ  6'b000110