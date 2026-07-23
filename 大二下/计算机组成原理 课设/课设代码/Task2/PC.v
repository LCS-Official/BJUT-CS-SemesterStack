/*
 * --------------------------------------------------------------------
 * 模块名称: PC (Program Counter)
 * 描述:     一个带有写使能和异步复位的32位程序计数器。
 * --------------------------------------------------------------------
 */
module PC(clk, reset, NPC, PC, pcwr);
	  input clk, reset, pcwr;
	  input [31:0]NPC;
	  output reg[31:0]PC;
	  always @ (posedge clk, posedge reset)
	  begin
		 if (reset) PC = 32'h0000_3000;
		 else if (pcwr) PC = NPC;
	  end
endmodule 
