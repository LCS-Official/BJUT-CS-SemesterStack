module mux8_1(in1, in2, in3, in4, in5, in6, in7, in8, sel, out);
	input [2:0] sel;
	input [31:0] in1, in2, in3, in4, in5, in6, in7, in8;
	output [31:0] out;
	reg [31:0] out;
	always @ (sel)
		begin
			case(sel)
				3'b000: out = in1;
				3'b001: out = in2;
				3'b010: out = in3;
				3'b011: out = in4;
				3'b100: out = in5;
				3'b101: out = in6;
				3'b110: out = in7;
				3'b111: out = in8;
				default: out = 32'b0;
			endcase
		end
endmodule