module scanner(clk, I_ROW, I_COL);
	input clk;
	
	output reg [15:0] I_ROW = 16'b0;
	output reg [3:0] I_COL = 4'b0;

	always@(posedge clk)
		if (I_COL < 16)
			I_COL <= I_COL + 1;
		else
			I_COL <= 4'b0;
			
	always@(I_COL)
		case(I_COL)
			0:I_ROW = 16'b1100_0000_0000_0011;//corner
			1:I_ROW = 16'b1000_0000_0000_0001;//corner
			2:I_ROW = 16'b0001_1111_1111_1000;//L
			3:I_ROW = 16'b0000_0000_0000_1000;//L
			4:I_ROW = 16'b0000_0000_0000_1000;//L
			5:I_ROW = 16'b0000_0000_0000_1000;//L
			6:I_ROW = 16'b0000_0000_0000_1000;//L
			7:I_ROW = 16'b0000_0000_0000_0000;//BLANK
			8:I_ROW = 16'b0000_0111_1110_0000;//C
			9:I_ROW = 16'b0000_1000_0001_0000;//C
			10:I_ROW = 16'b0001_0000_0000_1000;//C
			11:I_ROW = 16'b0001_0000_0000_1000;//C
			12:I_ROW = 16'b0000_1000_0001_0000;//C
			13:I_ROW = 16'b0000_0100_0010_0000;//C
			14:I_ROW = 16'b1000_0000_0000_0001;//corner
			15:I_ROW = 16'b1100_0000_0000_0011;//corner
			default:I_ROW = 16'b0;
		endcase
endmodule