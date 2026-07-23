module AR(clk, ar_in, ar_out);
	input clk;
	input [31:0] ar_in;
	output reg [31:0] ar_out;
  
	always @ (posedge clk)
		ar_out <= ar_in;
  
endmodule