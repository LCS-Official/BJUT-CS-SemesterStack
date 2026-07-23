module frequency_divider_1015(
    input clk_50mhz_hjq,           // 输入 50 MHz 时钟
    output reg clk_100hz_hjq       // 输出 100 Hz 时钟
);

	reg [31:0] cnt1_hjq;            // 计数器
	parameter A = 500000;       // 50 MHz / 100 Hz = 500,000
	//parameter A = 2;
	
	always @(posedge clk_50mhz_hjq) 
		begin
			if (cnt1_hjq < A/2 - 1) begin
				cnt1_hjq <= cnt1_hjq + 1'b1;        // 计数器加 1
			end else begin
				cnt1_hjq <= 0;                  // 重置计数器
				clk_100hz_hjq <= ~clk_100hz_hjq;    // 取反输出时钟信号，生成 100 Hz 时钟
			end
		end

endmodule
