module BCD_7seg(n_en, LED_in, LED_out, sel);
	input n_en;
	input [3:0] LED_in;
	output sel;
	output [6:0] LED_out;
	reg [6:0] LED_out;
	assign sel = 1'b0;
		always @ (n_en, LED_in)
			if(~n_en)
				begin
					case(LED_in)
						4'b0000: LED_out = 7'b1111110;
						4'b0001: LED_out = 7'b0110000;
						4'b0010: LED_out = 7'b1101101;
						4'b0011: LED_out = 7'b1111001;
						4'b0100: LED_out = 7'b0110011;
						4'b0101: LED_out = 7'b1011011;
						4'b0110: LED_out = 7'b1011111;
						4'b0111: LED_out = 7'b1110000;
						4'b1000: LED_out = 7'b1111111;
						4'b1001: LED_out = 7'b1111011;
						4'b1010: LED_out = 7'b1110111;
						4'b1011: LED_out = 7'b0011111;
						4'b1100: LED_out = 7'b0001101;
						4'b1101: LED_out = 7'b0111101;
						4'b1110: LED_out = 7'b1001111;
						4'b1111: LED_out = 7'b1000111;
						default: LED_out = 7'b0000000;
					endcase
				end
			else LED_out = 7'b0000000;
endmodule