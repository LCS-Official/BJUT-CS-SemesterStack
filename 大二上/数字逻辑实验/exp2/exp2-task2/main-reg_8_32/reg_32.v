module reg_32(clk, rst_n, in, load, out);
	input clk, rst_n, load;
	input [31:0] in;
	output [31:0] out;
	reg [31:0] out;
	always @ (posedge clk, negedge rst_n)
		if (~rst_n)
			out <= 0;
		else if (load == 1)
			out <= in;
endmodule