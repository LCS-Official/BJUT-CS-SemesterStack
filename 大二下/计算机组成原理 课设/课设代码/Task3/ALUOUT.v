module ALUOUT(clk, aluout_in, aluout_out);
	input clk;
	input [31:0] aluout_in;
	output reg [31:0] aluout_out;

	always @ (posedge clk)
		aluout_out <= aluout_in;
  
endmodule
  