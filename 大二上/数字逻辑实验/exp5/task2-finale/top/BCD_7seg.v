module BCD_7seg(n_en, data, out, sel);
	input n_en;
	input [3:0] data;
	output [6:0] out;
	output sel;
	reg [6:0] out;
	assign sel = 1'b0;
		always @ (n_en, data)
			if(~n_en)
				begin
					case(data)
						4'b0000: out = 7'b1111110;
						4'b0001: out = 7'b0110000;
						4'b0010: out = 7'b1101101;
						4'b0011: out = 7'b1111001;
						4'b0100: out = 7'b0110011;
						4'b0101: out = 7'b1011011;
						4'b0110: out = 7'b1011111;
						4'b0111: out = 7'b1110000;
						4'b1000: out = 7'b1111111;
						4'b1001: out = 7'b1111011;
						4'b1010: out = 7'b1110111;
						4'b1011: out = 7'b0011111;
						4'b1100: out = 7'b0001101;
						4'b1101: out = 7'b0111101;
						4'b1110: out = 7'b1001111;
						4'b1111: out = 7'b1000111;
						default: out = 7'b0000000;
					endcase
				end
			else out = 7'b0000000;
endmodule