/*
 * 模块名称: mips
 * 文件名称: mips.v
 * 描述:     MIPS单周期处理器顶层模块。
 */

`include "defines.v"

module mips(
    input clk,
    input rst
);

    // ------------------- 内部信号线 -------------------
    
    // 连接 datapath 和 controller 的信号线
    wire [31:0] w_instr;
    wire        w_alu_zero;
    wire        w_alu_overflow; // --更新点--: 新增溢出状态信号线
    
    // 连接 controller 到 datapath 的信号线
    wire        w_reg_write;
    wire        w_ext_op;
    wire [3:0]  w_alu_op;
    wire [1:0]  w_pc_src;
    wire        w_reg_dst;
    wire        w_alu_src;
    wire        w_mem_write;
    wire [1:0]  w_wb_sel;
	 wire        w_GPR_RD1_Sign;
    wire        w_jal_write;
    wire        w_ovf_write_en; // --更新点--: 新增溢出处理使能信号线

    // ------------------- 模块实例化与连接 -------------------

    // 1. 实例化数据通路
    //使用最终版的端口列表进行连接
    datapath datapath_unit (
        .clk(clk),
        .rst(rst),
        .RegWrite(w_reg_write),
        .ExtOp(w_ext_op),
        .ALUOp(w_alu_op),
        .PCSrc(w_pc_src),
        .RegDst(w_reg_dst),
        .ALUSrc(w_alu_src),
        .MemWrite(w_mem_write),
        .WriteBackSel(w_wb_sel),
        .JAL_Write(w_jal_write),
        .Ovf_WriteEnable(w_ovf_write_en), // 连接新端口
        .Instr(w_instr),
		  .GPR_RD1_Sign(w_GPR_RD1_Sign),
        .ALU_Zero(w_alu_zero),
        .ALU_Overflow(w_alu_overflow)     // 连接新端口
    );

    // 2. 实例化控制器
    //  使用最终版的端口列表进行连接
    controller controller_unit (
        .Instr(w_instr),
        .ALU_Zero(w_alu_zero),
        .ALU_Overflow(w_alu_overflow),   // 连接新端口
        .RegWrite(w_reg_write),
        .ExtOp(w_ext_op),
        .ALUOp(w_alu_op),
        .PCSrc(w_pc_src),
        .RegDst(w_reg_dst),
        .ALUSrc(w_alu_src),
        .MemWrite(w_mem_write),
        .WriteBackSel(w_wb_sel),
		  .GPR_RD1_Sign(w_GPR_RD1_Sign),
        .JAL_Write(w_jal_write),
        .Ovf_WriteEnable(w_ovf_write_en) // 连接新端口
    );

endmodule