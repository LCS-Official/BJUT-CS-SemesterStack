/*
 * --------------------------------------------------------------------
 * 模块名称: pc (Program Counter)
 * 描述:     一个带有写使能和异步复位的32位程序计数器。
 * --------------------------------------------------------------------
 */

module pc(clk, rst, NPC, PC, PCWrite);
	input clk, rst, PCWrite;
	input [31:0]NPC;
	output reg[31:0]PC;
	always @ (posedge clk, posedge rst) begin
		if (rst) begin
			PC = 32'h0000_3000;
		end
		else if (PCWrite) PC = NPC;
	end
endmodule 
