module BR(clk, br_in, br_out);
	input clk;
	input [31:0] br_in;
	output reg [31:0] br_out;
  
	always @ (posedge clk)
		br_out <= br_in;
  
endmodule



