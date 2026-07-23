// =================================================================
// defines.v
// MIPS处理器全局宏定义文件
// =================================================================

// ---------- 1. 指令操作码 (Opcode) 定义 ----------
// R-type 指令共用的操作码
`define OP_RTYPE   6'h00  // 000000

// I-type 指令
`define OP_ADDI    6'h08  // 001000
`define OP_ADDIU   6'h09  // 001001
`define OP_LW      6'h23  // 100011
`define OP_LB      6'h20  // 100000
`define OP_LUI     6'h0F  // 001111
`define OP_ORI     6'h0D  // 001101
`define OP_SW      6'h2B  // 101011
`define OP_SB      6'h28  // 101000
`define OP_BEQ     6'h04  // 000100

// J-type 指令
`define OP_J       6'h02  // 000010
`define OP_JAL     6'h03  // 000011


// ---------- 2. R-type 指令功能码 (Function Code) 定义 ----------
`define F_ADDU     6'h21  // 100001
`define F_SUBU     6'h23  // 100011
`define F_SLT      6'h2A  // 101010
`define F_JR       6'h08  // 001000


// ---------- 3. 控制信号参数化宏定义 ----------

// -- RegDst (reg_sel) --
// 选择写入哪个目标寄存器
`define REGDST_RT  2'b00  // 目标寄存器是 rt (I-type, lw)
`define REGDST_RD  2'b01  // 目标寄存器是 rd (R-type)
`define REGDST_RA  2'b10  // 目标寄存器是 $ra(31) (jal)

// -- MemToReg (wd_sel) --
// 选择写回寄存器的数据来源
`define MEMTOREG_ALU 2'b00  // 数据来自 ALU 计算结果
`define MEMTOREG_MEM 2'b01  // 数据来自数据存储器
`define MEMTOREG_PC4 2'b10  // 数据来自 PC+4 (jal)

// -- PCSrc (npc_sel) --
// 选择下一条指令的地址来源
`define PCSRC_PC4    2'b00  // 来源: PC+4 (默认)
`define PCSRC_BRANCH 2'b01  // 来源: 分支目标地址 (beq)
`define PCSRC_JUMP   2'b10  // 来源: 跳转目标地址 (j, jal)
`define PCSRC_JR     2'b11  // 来源: 寄存器地址 (jr)

// -- ExtOp (ext_op) --
// 选择立即数扩展方式
`define EXTOP_ZERO   2'b00  // 零扩展 (逻辑指令如 ori)
`define EXTOP_SIGN   2'b01  // 符号扩展 (算术和访存指令)
`define EXTOP_LUI    2'b10  // LUI特殊处理 (高16位)