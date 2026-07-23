module BCD_7seg_1015(n_en, LED_in, LED_out);
	input n_en;
	input [3:0] LED_in;
	output [6:0] LED_out;
	reg [6:0] LED_out;

		always @ (n_en, LED_in)
			if(~n_en)
				begin
					case(LED_in)
						4'b0000: LED_out = 7'b1111110; //0
						4'b0001: LED_out = 7'b0110000; //1
						4'b0010: LED_out = 7'b1101101; //2
						4'b0011: LED_out = 7'b1111001; //3
						4'b0100: LED_out = 7'b0110011; //4
						4'b0101: LED_out = 7'b1011011; //5
						4'b0110: LED_out = 7'b1011111; //6
						4'b0111: LED_out = 7'b1110000; //7
						4'b1000: LED_out = 7'b1111111; //8
						4'b1001: LED_out = 7'b1111011; //9
						default: LED_out = 7'b0000000; // 超出范围时关闭显示
					endcase
				end 
			else 
				LED_out = 7'b0000000;
endmodule