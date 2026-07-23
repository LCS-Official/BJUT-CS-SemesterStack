module DR(clk, dr_in, dr_out);
	input clk;
	input [31:0] dr_in;
	output reg [31:0] dr_out;
  
	always @ (posedge clk)
		dr_out <= dr_in;

endmodule
