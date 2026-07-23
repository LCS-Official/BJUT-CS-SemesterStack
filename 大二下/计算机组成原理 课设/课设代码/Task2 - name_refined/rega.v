/*
 * --------------------------------------------------------------------
 * 模块名称: rega
 * 描述: ALU输出的第一个结果寄存器
 * --------------------------------------------------------------------
 */
module rega(clk, din, dout);
	input clk;
	input [31:0]din;
	output reg[31:0]dout;
	always @ (posedge clk)
		dout = din;
endmodule