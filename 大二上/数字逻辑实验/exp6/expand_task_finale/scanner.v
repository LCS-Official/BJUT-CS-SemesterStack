module scanner(clk, I_ROW, I_COL, clk_1hz);
	input clk,clk_1hz;
	output reg [15:0] I_ROW = 16'b0;
	output reg [3:0] I_COL = 4'b0;
	reg [10:0] flag;
	reg [15:0] graph [31:0];
	initial 
		begin
			graph [0]=16'b1100_0000_0000_0011;//corner
			graph [1]=16'b1000_0000_0000_0001;//corner
			graph [2]=16'b0001_1111_1111_1000;//L
			graph [3]=16'b0000_0000_0000_1000;//L
			graph [4]=16'b0000_0000_0000_1000;//L
			graph [5]=16'b0000_0000_0000_1000;//L
			graph [6]=16'b0000_0000_0000_1000;//L
			graph [7]=16'b0000_0000_0000_0000;//BLANK
			graph [8]=16'b0000_0111_1110_0000;//C
			graph [9]=16'b0000_1000_0001_0000;//C
			graph [10]=16'b0001_0000_0000_1000;//C
			graph [11]=16'b0001_0000_0000_1000;//C
			graph [12]=16'b0000_1000_0001_0000;//C
			graph [13]=16'b0000_0100_0010_0000;//C
			graph [14]=16'b0000_0000_0000_0000;//BLANK
			graph [15]=16'b0000_0000_0000_0000;//BLANK
			graph [16]=16'b0000_1110_0010_0000;//S
			graph [17]=16'b0001_0001_0001_0000;//S
			graph [18]=16'b0000_1000_1111_0000;//S
			graph [19]=16'b0000_0001_0000_0000;//t
			graph [20]=16'b0000_0011_1110_0000;//t
			graph [21]=16'b0000_0001_0001_0000;//t
			graph [22]=16'b0000_0000_1110_0000;//a
			graph [23]=16'b0000_0001_0001_0000;//a
			graph [24]=16'b0000_0000_1110_0000;//a
			graph [25]=16'b0000_0000_0001_0000;//a
			graph [26]=16'b0000_0001_0000_0000;//t
			graph [27]=16'b0000_0011_1110_0000;//t
			graph [28]=16'b0000_0001_0001_0000;//t
			graph [29]=16'b0000_0001_1110_0000;//e
			graph [30]=16'b1000_0010_1001_0001;//corner&e
			graph [31]=16'b1100_0001_1010_0011;//corner&e
		end
	
	always@(posedge clk)
		if (I_COL < 16)
			I_COL <= I_COL + 1;
		else
			I_COL <= 4'b0;
	
	always@(posedge clk_1hz)
		if (flag < 18)
			flag <= flag + 1;
		else
			flag <= 0;

	
	always@(I_COL, flag)
		if (flag>2)
			begin
				I_ROW = graph[I_COL+flag-2];
			end
		else begin
					case(flag)
						0:
							I_ROW = graph[I_COL];
						1:
							I_ROW = graph[I_COL+16];
						2:
							I_ROW = graph[I_COL];
					endcase
				end

endmodule