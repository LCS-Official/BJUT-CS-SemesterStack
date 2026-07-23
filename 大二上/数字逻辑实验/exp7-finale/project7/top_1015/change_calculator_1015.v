module change_calculator_1015(
	 input clk_hjq,                    // 时序判断
    input [7:0] vendingmachine_gain,  // 投币金额
    input [7:0] fee_deduct,     		  // 花费金额
    output reg [7:0] change,   		  // 零钱数目
    output reg insufficient = 0    	  // 不足信号
);

	always @(posedge clk_hjq) 
		begin
			if (vendingmachine_gain >= fee_deduct) 
				begin
					change = vendingmachine_gain - fee_deduct;  // 计算零钱
					insufficient = 0; 	  // 金额足够
				end else begin
					change = 8'b00000000;  // 如果金额不足，零钱为0
					insufficient = 1;      // 设置不足信号
				end
		end

endmodule
