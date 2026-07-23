module vending_machine_1015(
    input clk_hjq,            // 时钟信号
    input coin_1,             // 1角硬币投币口（开关控制）
    input coin_5,             // 5角硬币投币口
    input coin_10,            // 10角硬币投币口
    input bill_10,            // 1元纸币投币口
    input bill_50,            // 5元纸币投币口
    input confirm,            // 确认投币按钮
    output reg [7:0] total    // 总金额（以角为单位）
);
 
    // 中间存储变量
    reg [7:0] total_amount = 0;    // 当前投币总金额

	 always @(posedge clk_hjq) 		//采用时序
			begin
				 // 判断硬币和纸币的上升沿并进行累加
				 if (coin_1) begin
					  total_amount <= total_amount + 8'd1;    // 1角硬币
				 end else if (coin_5) begin
					  total_amount <= total_amount + 8'd5;    // 5角硬币
				 end else if (coin_10) begin
					  total_amount <= total_amount + 8'd10;   // 10角硬币
				 end else if (bill_10) begin
					  total_amount <= total_amount + 8'd10;   // 1元纸币
				 end else if (bill_50) begin
					  total_amount <= total_amount + 8'd50;   // 5元纸币
				 end
			end


    // 当确认按钮被按下时，输出当前的总金额
    always @(posedge clk_hjq) 
		 begin
				// 如果确认按钮按下，将总金额输出
				total <= total_amount;
		 end

endmodule