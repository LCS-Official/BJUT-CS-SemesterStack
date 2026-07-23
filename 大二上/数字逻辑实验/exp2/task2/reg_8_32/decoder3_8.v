module decoder3_8(in, out1, out2, out3, out4, out5, out6, out7, out8);
	input [2:0] in;
	output out1, out2, out3, out4, out5, out6, out7, out8;
	reg out1, out2, out3, out4, out5, out6, out7, out8;
		always @ (in)
		begin
			case(in)
				3'b000: {out1, out2, out3, out4, out5, out6, out7, out8} = 8'b10000000;
				3'b001: {out1, out2, out3, out4, out5, out6, out7, out8} = 8'b01000000;
				3'b010: {out1, out2, out3, out4, out5, out6, out7, out8} = 8'b00100000;
				3'b011: {out1, out2, out3, out4, out5, out6, out7, out8} = 8'b00010000;
				3'b100: {out1, out2, out3, out4, out5, out6, out7, out8} = 8'b00001000;
				3'b101: {out1, out2, out3, out4, out5, out6, out7, out8} = 8'b00000100;
				3'b110: {out1, out2, out3, out4, out5, out6, out7, out8} = 8'b00000010;
				3'b111: {out1, out2, out3, out4, out5, out6, out7, out8} = 8'b00000001;
				default: {out1, out2, out3, out4, out5, out6, out7, out8} = 8'b00000000;
			endcase
		end
endmodule