module keyboard_recognition(swc, swr, clk, reset, flag, keyout);
    input clk, reset;
    input [3:0] swc;
    output reg [3:0] swr;
    output reg flag;
    output reg [3:0] keyout;
		always @ (posedge clk) 
			begin
				if (reset)
					swr = 4'b1111;
				else
					begin
						case (swr)
							4'b1110: swr = 4'b1101;
							4'b1101: swr = 4'b1011;
							4'b1011: swr = 4'b0111;
							4'b0111: swr = 4'b1110;
							default: swr = 4'b1110;
						endcase
					end
			end
		always @ (posedge clk)
			begin
				case ({swr, swc})
					8'b1110_1110: {flag, keyout} <= 5'b1_0000;
					8'b1110_1101: {flag, keyout} <= 5'b1_0001;
					8'b1110_1011: {flag, keyout} <= 5'b1_0010;
					8'b1110_0111: {flag, keyout} <= 5'b1_0011;
					8'b1101_1110: {flag, keyout} <= 5'b1_0100;
					8'b1101_1101: {flag, keyout} <= 5'b1_0101;
					8'b1101_1011: {flag, keyout} <= 5'b1_0110;
					8'b1101_0111: {flag, keyout} <= 5'b1_0111;
					8'b1011_1110: {flag, keyout} <= 5'b1_1000;
					8'b1011_1101: {flag, keyout} <= 5'b1_1001;
					8'b1011_1011: {flag, keyout} <= 5'b1_1010;
					8'b1011_0111: {flag, keyout} <= 5'b1_1011;
					8'b0111_1110: {flag, keyout} <= 5'b1_1100;
					8'b0111_1101: {flag, keyout} <= 5'b1_1101;
					8'b0111_1011: {flag, keyout} <= 5'b1_1110;
					8'b0111_0111: {flag, keyout} <= 5'b1_1111;
					default: {flag, keyout} <= {flag, keyout};
				endcase
			end
endmodule