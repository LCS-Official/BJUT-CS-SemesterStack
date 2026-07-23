/*
 * --------------------------------------------------------------------
 * 模块名称: regb
 * 描述: ALU输出的第二个结果寄存器
 * --------------------------------------------------------------------
 */
module regb(clk, din, dout);
	input clk;
	input [31:0]din;
	output reg[31:0]dout;
	always @ (posedge clk)
		dout = din;
endmodule