module IR(IR_Wr, irin, irout, clk);
	input clk, IR_Wr;
	input [31:0] irin;
	output reg [31:0] irout;
  
	always @ (posedge clk)
		if(IR_Wr)
			irout <= irin;

endmodule