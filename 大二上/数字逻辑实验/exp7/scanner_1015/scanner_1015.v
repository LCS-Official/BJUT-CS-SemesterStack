module scanner_1015(
	input clk_hjq,
	output reg [7:0] ds_hjq = 8'b0,
	output reg [2:0] sel_hjq = 3'b0
);

	always@(posedge clk_hjq)
		begin 
			if(sel_hjq == 7)
				sel_hjq <= 0;
			else
				sel_hjq <= sel_hjq +1;
		end
		
	always@(sel_hjq)
		begin
			case(sel_hjq)
				0:ds_hjq=8'b1111_1110;
				1:ds_hjq=8'b1111_1101;
				2:ds_hjq=8'b1111_1011;
				3:ds_hjq=8'b1111_0111;
				4:ds_hjq=8'b1110_1111;
				5:ds_hjq=8'b1101_1111;
				6:ds_hjq=8'b1011_1111;
				7:ds_hjq=8'b0111_1111;
				default:ds_hjq=8'b0;
			endcase
		end
endmodule