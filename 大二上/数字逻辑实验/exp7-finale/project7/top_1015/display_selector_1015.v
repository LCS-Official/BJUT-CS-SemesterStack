module display_selector_1015(
	input n_en,
	input [2:0] sel_hjq, 		//从8个LED数码管中选择
	input [7:0] vendingmachine_out,distance_out,change_out,fee_out,
	output reg [3:0] out
);
	
	always @(sel_hjq)
		begin
			if(!n_en)
				begin
					case(sel_hjq)
					  3'b000 : out = change_out % 10;
					  3'b001 : out = change_out / 10;
					  3'b010 : out = vendingmachine_out % 10;
					  3'b011 : out = vendingmachine_out / 10;
					  3'b100 : out = fee_out % 10;
					  3'b101 : out = fee_out / 10;
					  3'b110 : out = distance_out % 10; //dis_ones
					  3'b111 : out = distance_out / 10; //dis_tenth
					endcase
				end 
					else
						out = 4'b0000;
		end
endmodule