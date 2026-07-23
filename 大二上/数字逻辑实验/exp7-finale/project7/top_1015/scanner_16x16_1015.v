module scanner_16x16_1015(
	input  buy, clk_1hz, insufficient, n_en,  clk_1khz_hjq, 
	input [7:0] dis_in,
	output reg [15:0] I_ROW = 16'b0,
	output reg [3:0] I_COL = 4'b0,
	output reg bought = 0,
	output reg clr_hjq = 0					  // clr_hjq 输出信号
);
	reg [10:0] flag1, flag2;
	reg [15:0] graph [95:0];
	reg insuff_buy;							  // 试图在钱不够时购买
	reg [15:0] clr_counter = 0;			  // 计数器，用于延时控制 clr_hjq 和 bought 的复位
	
	initial 
		begin
			graph [0]=16'b0000001000000000; //请
			graph [1]=16'b0100001000000000;
			graph [2]=16'b0011001111111110;
			graph [3]=16'b0000000000000100;
			graph [4]=16'b0000000000001000;
			graph [5]=16'b0010001000000000;
			graph [6]=16'b0010101011111111;
			graph [7]=16'b0010101010101000;
			graph [8]=16'b0010101010101000;
			graph [9]=16'b1111111010101000;
			graph [10]=16'b0010101010101010;
			graph [11]=16'b0010101010101001;
			graph [12]=16'b0010101011111110;
			graph [13]=16'b0010001000000000;
			graph [14]=16'b0000001000000000;
			graph [15]=16'b0000000000000000;
			
			graph [16]=16'b0000100000100000; //投
			graph [17]=16'b0000100000100010;
			graph [18]=16'b0000100001000001;
			graph [19]=16'b1111111111111110;
			graph [20]=16'b0000100010000000;
			graph [21]=16'b0000100100000000;
			graph [22]=16'b0000001000000001;
			graph [23]=16'b0000010100000001;
			graph [24]=16'b0111100111000010;
			graph [25]=16'b0100000100110100;
			graph [26]=16'b0100000100001000;
			graph [27]=16'b0100000100010100;
			graph [28]=16'b0111100100100010;
			graph [29]=16'b0000010111000001;
			graph [30]=16'b0000010000000001;
			graph [31]=16'b0000000000000000;
			
			graph [32]=16'b0000000000000000; //币
			graph [33]=16'b0010000000000000;
			graph [34]=16'b0010011111111000;
			graph [35]=16'b0010010000000000;
			graph [36]=16'b0010010000000000;
			graph [37]=16'b0010010000000000;
			graph [38]=16'b0010010000000000;
			graph [39]=16'b0111111111111111;
			graph [40]=16'b0100010000000000;
			graph [41]=16'b0100010000000000;
			graph [42]=16'b0100010000010000;
			graph [43]=16'b0100010000001000;
			graph [44]=16'b1100011111110000;
			graph [45]=16'b0100000000000000;
			graph [46]=16'b0000000000000000;
			graph [47]=16'b0000000000000000;
			
			graph [48]=16'b0000000000001000; //不
			graph [49]=16'b0100000000010000;
			graph [50]=16'b0100000000100000;
			graph [51]=16'b0100000001000000;
			graph [52]=16'b0100000010000000;
			graph [53]=16'b0100000100000000;
			graph [54]=16'b0100001000000000;
			graph [55]=16'b0100111111111111;
			graph [56]=16'b0111000000000000;
			graph [57]=16'b0100001000000000;
			graph [58]=16'b0100000100000000;
			graph [59]=16'b0100000010000000;
			graph [60]=16'b0100000001000000;
			graph [61]=16'b0100000000110000;
			graph [62]=16'b0000000000000000;
			graph [63]=16'b0000000000000000;
			
			graph [64]=16'b0000000000000001; //足
			graph [65]=16'b0000000000000010;
			graph [66]=16'b0000000000001100;
			graph [67]=16'b0111111001110000;
			graph [68]=16'b0100001000001000;
			graph [69]=16'b0100001000000100;
			graph [70]=16'b0100001000000010;
			graph [71]=16'b0100001111111110;
			graph [72]=16'b0100001000100010;
			graph [73]=16'b0100001000100010;
			graph [74]=16'b0100001000100010;
			graph [75]=16'b0111111000100010;
			graph [76]=16'b0000000000100010;
			graph [77]=16'b0000000000000010;
			graph [78]=16'b0000000000000010;
			graph [79]=16'b0000000000000000;
			
			graph [80]=16'b0011111111111100; //出票！
			graph [81]=16'b0010000111100100;
			graph [82]=16'b0010001100100100;
			graph [83]=16'b0010010100110100;
			graph [84]=16'b0010100100101100;
			graph [85]=16'b0010111100110100;
			graph [86]=16'b0010100000110100;
			graph [87]=16'b0010111111101100;
			graph [88]=16'b0010100100110100;
			graph [89]=16'b0010100100100100;
			graph [90]=16'b0010111100100100;
			graph [91]=16'b0010100100100100;
			graph [92]=16'b0010100100100100;
			graph [93]=16'b0010111111110100;
			graph [94]=16'b0010100000101100;
			graph [95]=16'b0011111111111100;
		end
	
	always@(posedge clk_1khz_hjq)
		begin
			if (~n_en)
				begin
					if (I_COL < 16)
						I_COL <= I_COL + 1;           // 点阵扫描逻辑
					else
						I_COL <= 4'b0;
					
					if (!buy)								
						begin
							if (!insufficient)
								begin
									if(dis_in)
										bought <= 1;			// 如果点按了购买按钮，且钱够，指示已购买
										clr_hjq <= 1; 			// 出票信号置位
								end
							else
								insuff_buy <= 1;
						end
						
					if (!insufficient)
						insuff_buy <= 0;					// 若钱不够，则没法购买，触发不足信号
					
					if (clr_hjq)							// 如果 clr_hjq 置位，进入倒计时复位逻辑
						begin
							if (clr_counter < 2500) 	// 约 2.5 秒倒计时
								clr_counter <= clr_counter + 1;
							else
								begin
									clr_hjq <= 0;  		// 倒计时结束，清除 clr_hjq 信号
									bought <= 0;   		// 同时复位 bought 状态
									clr_counter <= 0; 	// 复位计数器
								end
						end
					
				end
			else
				begin
					bought <= 0;         				// 如果关机了，复位购买状态
					insuff_buy <= 0;     				// 复位 insufficient 标志
					clr_hjq <= 0;        				// 复位 clr_hjq 信号
					clr_counter <= 0;   					// 复位计数器
				end
		end
	
	always @(posedge clk_1hz) 
		begin
			if(~n_en)
				begin
					if (flag1 < 2)						   
						flag1 <= flag1 + 1;				
					else
						flag1 <= 0;
								
					if (flag2 < 1)
						flag2 <= flag2 + 1;				// 不足指示
					else
						flag2 <= 0;
				end
			else
					flag1 <= 0;
		end
	
	always @(I_COL, flag1, flag2)
		begin
			if (!bought)									//如果没有点击购买，则显示投币指导
				begin
					if (flag1 < 3)
						I_ROW = graph[I_COL + flag1*16];
				end
			else												//如果点击了购买，且钱够，出票！
				I_ROW = graph[I_COL + 80];
				
			if (insuff_buy)		
				begin											//如果点击了购买，但钱不够，展示不足字样
					case(flag2)
						0:I_ROW = graph[I_COL + 48];
						1:I_ROW = graph[I_COL + 64];
						default:I_ROW = graph[I_COL + 64];
					endcase
				end
		end

endmodule