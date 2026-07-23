module three_t(en, in, out);
	input en;
	input [31:0] in;
	output [31:0] out;
		assign out = (en == 1) ? in :32'bz;
endmodule