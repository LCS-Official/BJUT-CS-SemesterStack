module vending_machine_1015(
	input clk_hjq,							// 时钟信号
   input coin_1,							// 1角硬币投币口
   input bill_10,							// 1元纸币投币口
	input minus,							// 吐出钱币
   output reg [7:0] total_out = 0,	// 总金额
	input clr_hjq							// 重置总金额（为1时清零）
);

	reg [7:0] total_amount = 0;    	// 当前投币总金额

	always @(posedge clk_hjq)
		begin
			if (!coin_1) 
				total_amount <= total_amount + 8'd1;	// 1角硬币			
			else if (!bill_10)
				total_amount <= total_amount + 8'd10;	// 1元纸币
			else if (!minus && total_amount > 0)
				total_amount <= total_amount - 8'd1;	// minus
				 
			if(clr_hjq)	//清零
				total_amount <= 0;
						
			total_out <= total_amount;
		end

endmodule