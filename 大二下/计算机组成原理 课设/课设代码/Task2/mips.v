// mips.v
// MIPS处理器全局定义文件
// 
module mips(clk, rst);
	  input clk;
	  input rst;
	  wire [31:0] insout, nxtpc, curpc, pc_add4, wd, sbout, lbout;
	  wire [31:0] busA, busB, B, extout, alu_out, dmout, busAout, busBout, alu_outout;
	  wire [25:0] imm26;
	  wire [15:0] imm16;
	  wire [5:0] op, func;
	  wire [4:0] rs, rt, rd, rw;
	  wire [2:0] alu_op;
	  wire [1:0] reg_sel, wd_sel, npc_sel, ext_op, sb_sel, lb_sel;
	  wire overflow, zero, we, regwrite, alu_sel, addi, slt, irwr, pcwr, sben, lben;
	  
	  assign rw = (reg_sel==0) ? rt : (reg_sel==1) ? rd : 5'b11111;
	  assign wd = (wd_sel==0) ? alu_outout : (wd_sel==1) ? lbout : pc_add4;
	  assign B = alu_sel ? extout : busBout;
	  assign sbout = busBout;
	  assign lbout = dmout;

// 实例化模块
	  Controller Controller(rst, clk, op, func, reg_sel, alu_op, wd_sel, we, npc_sel, ext_op, regwrite, alu_sel, addien, slten, lben, sben, pcwr, irwr, zero);
	  
	  ALU ALU(busAout, B, alu_op, zero, alu_out, overflow, slten, addien);
	  dm_1k DM(alu_outout[9:0], sbout, we, clk, dmout, lben, sben);
	  EXT EXT(imm26[15:0], extout, ext_op);
	  GPR GPR(clk, rst, rs, rt, rw, wd, regwrite, busA, busB, overflow);
	  im_1k IM(curpc[9:0], insout);
	  NPC NPC(curpc, imm26, busA, npc_sel, zero, nxtpc, pc_add4);
	  PC PC(clk, rst, nxtpc, curpc, pcwr);
	  IR IR(clk, insout, rs, rt, rd, func, op, imm26, irwr);
	  rega RegA(clk, busA, busAout);
	  regb RegB(clk, busB, busBout);
	  regaluout RegALUOut(clk, alu_out, alu_outout);

endmodule