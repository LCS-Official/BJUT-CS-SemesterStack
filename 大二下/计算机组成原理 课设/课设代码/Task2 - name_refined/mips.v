/*
 * --------------------------------------------------------------------
 * 模块名称: mips
 * 文件名称: mips.v
 * 描述:     MIPS多周期处理器顶层模块。
 * --------------------------------------------------------------------
 */
`include "defines.v"
module mips(clk, rst);
	input clk;
	input rst;

	// 信号线定义
	wire [31:0] insout, nxtpc, curpc, pc_add4, wd, sbout, lbout;
	wire [31:0] busA, busB, B, extout, alu_out, dmout, busAout, busBout, alu_outout;
	wire [25:0] imm26;
	wire [5:0] 	op_wire, func_wire;
	wire [4:0] 	rs, rt, rd, rw;
	wire [2:0] 	ALUOp;
	wire [1:0] 	reg_sel, wd_sel, PCSrc, ExtOp, sb_sel, lb_sel;
	wire 			overflow, zero_wire, we, RegWrite, alu_sel, addien, slt_en, IRWrite, pcwr, sb_en, lb_en;

	// assign 语句
	assign rw = (reg_sel==0) ? rt : (reg_sel==1) ? rd : 5'b11111;
	assign wd = (wd_sel==0) ? alu_outout : (wd_sel==1) ? lbout : pc_add4;
	assign B = alu_sel ? extout : busBout;
	assign sbout = busBout;
	assign lbout = dmout;

	//----------------------------------------------------
	// 模块实例化
	//----------------------------------------------------
	controller controller_unit (
    // 输入
    .clk        (clk),
    .rst        (rst),
    .op         (op_wire),
    .func       (func_wire),
    .zero       (zero_wire),

    // 输出控制信号
    .PCSrc      (PCSrc),
    .PCWrite    (pcwr),
    .IRWrite    (IRWrite),
    .RegWrite   (RegWrite),
    .ExtOp      (ExtOp),
    .ALUOp      (ALUOp),
    .ALUSrc     (alu_sel),
    .RegDst     (reg_sel),
    .MemToReg   (wd_sel),
    .MemWrite   (we),
    .lb_en      (lb_en),
    .sb_en      (sb_en),
    .slt_en     (slt_en),
    .addi_en    (addien)
);
	pc PC( .clk(clk), .rst(rst), .NPC(nxtpc), .PC(curpc), .PCWrite(pcwr) );
	im IM( .addr(curpc[9:0]), .dout(insout) );
	ir IR( .clk(clk), .ins(insout), .rs(rs), .rt(rt), .rd(rd), .func(func_wire), .OpCode(op_wire), .imm26(imm26), .IRWrite(IRWrite) );
	gpr GPR( .clk(clk), .rst(rst), .rs(rs), .rt(rt), .rw(rw), .wd(wd), .RegWrite(RegWrite), .busA(busA), .busB(busB), .addi_overflow(overflow) );
	ext EXT( .imm16(imm26[15:0]), .imm32(extout), .ExtOp(ExtOp) );
	npc NPC( .PC(curpc), .Instr_25_0(imm26), .register(busA), .PCSrc(PCSrc), .zero(zero_wire), .NPC(nxtpc), .pc_add4(pc_add4) );

	// 中间寄存器
	rega RegA( .clk(clk), .din(busA), .dout(busAout) );
	regb RegB( .clk(clk), .din(busB), .dout(busBout) );

	// ALU 单元
	// 注意: 请确认您的 alu 模块定义与此处的端口连接一致
	// 特别是 slten 和 addien，在优化后的 controller.v 中已整合，此处直接连接
	alu ALU( .A(busAout), .B(B), .ALUOp(ALUOp), .zero(zero_wire), .alu_out(alu_out), .slt(slt_en), .addi(addien) );
	regaluout RegALUOut( .clk(clk), .din(alu_out), .dout(alu_outout) );

	// 数据存储器
	dm DM( .addr(alu_outout[9:0]), .din(sbout), .we(we), .clk(clk), .dout(dmout), .lb_en(lb_en), .sb_en(sb_en) );

endmodule