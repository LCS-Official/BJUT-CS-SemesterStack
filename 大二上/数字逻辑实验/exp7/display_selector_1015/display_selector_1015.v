module display_selector_1015(
	input n_en,
	input [2:0] sel_hjq, 		//从8个LED数码管中选择
	output reg [3:0] out,
	input [3:0] in8,in7,in6,in5,in4,in3,in2,in1
);
	
	always @(sel_hjq)
		begin
			if(!n_en)
				begin
					case(sel_hjq)
					  3'b000 : out = in1;
					  3'b001 : out = in2;
					  3'b010 : out = in3;
					  3'b011 : out = in4;
					  3'b100 : out = in5;
					  3'b101 : out = in6;
					  3'b110 : out = in7;
					  3'b111 : out = in8;
					endcase
				end else
						out = 4'b0000;
		end
endmodule