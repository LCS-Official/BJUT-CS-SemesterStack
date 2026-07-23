// defines.v

// 指令 Opcode 定义 (MIPS-Lite2)
`define OP_RTYPE   6'b000000 // R-Type 指令
`define OP_ADDI    6'b001000 // addi
`define OP_ADDIU   6'b001001 // addiu
`define OP_ORI     6'b001101 // ori
`define OP_LUI     6'b001111 // lui
`define OP_LW      6'b100011 // lw
`define OP_SW      6'b101011 // sw
`define OP_LB      6'b100000 // lb
`define OP_SB      6'b101000 // sb
`define OP_BEQ     6'b000100 // beq
`define OP_J       6'b000010 // j
`define OP_JAL     6'b000011 // jal

// R-Type 指令的功能码 (funct)
`define FUNCT_ADDU  6'b100001 // addu
`define FUNCT_SUBU  6'b100011 // subu
`define FUNCT_JR    6'b001000 // jr
`define FUNCT_SLT   6'b101010 // slt

// ALU 控制信号定义
`define ALU_ADD     4'b0000
`define ALU_SUB     4'b0001
`define ALU_OR      4'b0010
`define ALU_SLT     4'b0011
`define ALU_LUI     4'b0100 // LUI特殊操作，将立即数左移16位

// 状态机状态定义 (FSM States)
`define S_FETCH     4'd0  // 取指
`define S_DECODE    4'd1  // 译码 & 读寄存器
`define S_EXEC_R    4'd2  // R-Type 执行
`define S_EXEC_I_ALU 4'd3  // I-Type (ALU) 执行
`define S_EXEC_MEM  4'd4  // 内存地址计算
`define S_MEM_READ  4'd5  // 内存读
`define S_MEM_WRITE 4'd6  // 内存写
`define S_WB_REG    4'd7  // R/I-Type 写回寄存器
`define S_WB_MEM    4'd8  // LW/LB 写回寄存器
`define S_BEQ       4'd9  // BEQ 分支
`define S_JUMP      4'd10 // J/JAL 跳转
`define S_JR        4'd11 // JR 跳转
`define S_ADDI_OVF  4'd12 // ADDI 溢出处理状态