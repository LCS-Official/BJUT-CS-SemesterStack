module frequency_divider_1015(
    input clk_50mhz_hjq,            // 输入 50 MHz 时钟
    output reg clk_1000hz_hjq,      // 输出 1000 Hz 时钟
	 output reg clk_1hz_hjq,
	 output reg clk_4hz_hjq,
	 output reg clk_20hz_hjq
);

	reg [31:0] cnt1_hjq;             // 计数器
	reg [31:0] cnt2_hjq;
	reg [31:0] cnt3_hjq;
	reg [31:0] cnt4_hjq;
	
	parameter A = 50000;             // 50 MHz / 1000 Hz = 5,0000
	parameter B = 12500000;          // 4Hz
	parameter C = 2500000;           // 20Hz
	parameter D = 50000000;          // 1Hz
	
	always @(posedge clk_50mhz_hjq) 
		begin
			if (cnt1_hjq < A/2 - 1) begin
				cnt1_hjq <= cnt1_hjq + 1'b1;          // 计数器加 1
			end else begin
				cnt1_hjq <= 0;                        // 重置计数器
				clk_1000hz_hjq <= ~clk_1000hz_hjq;    // 取反输出时钟信号，生成 1000 Hz 时钟
			end
		end
		
	always @(posedge clk_50mhz_hjq) 
		begin
			if (cnt2_hjq < B/2 - 1) begin
				cnt2_hjq <= cnt2_hjq + 1'b1;   
			end else begin
				cnt2_hjq <= 0;                 
				clk_4hz_hjq <= ~clk_4hz_hjq;
			end
		end
		
	always @(posedge clk_50mhz_hjq) 
		begin
			if (cnt3_hjq < C/2 - 1) begin
				cnt3_hjq <= cnt3_hjq + 1'b1;   
			end else begin
				cnt3_hjq <= 0;                 
				clk_20hz_hjq <= ~clk_20hz_hjq;
			end
		end
	
	always @(posedge clk_50mhz_hjq) 
		begin
			if (cnt4_hjq < D/2 - 1) begin
				cnt4_hjq <= cnt4_hjq + 1'b1;   
			end else begin
				cnt4_hjq <= 0;                 
				clk_1hz_hjq <= ~clk_1hz_hjq;
			end
		end
endmodule
