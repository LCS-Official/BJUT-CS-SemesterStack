module distance_1015(
	input clk_hjq,								// 时钟信号
   input [1:0] dis_in,  					// 4位输入   
   output reg [7:0] distance_result,   // 结果输出
	output reg [7:0] fee_result,        // 金额输出
	input clr_hjq,								// 重置
	input back_trip							// 往返
);

	reg [7:0] total_amount = 0;
	reg isbacktrip;
	
	always @(posedge clk_hjq) 
		begin
			if (!dis_in[0]) 
				total_amount <= total_amount + 8'd1;		
			else if (!dis_in[1] && total_amount > 0)
				total_amount <= total_amount - 8'd1;

			if(clr_hjq)
				begin
					total_amount <= 0;
					isbacktrip <= 0;
				end
						
			distance_result <= total_amount;
			
			if (!back_trip)
				begin
					if (!isbacktrip)
						isbacktrip <= 1;
					else
						isbacktrip <= 0;
				end
		end
	
	always @(*)
		if(isbacktrip)
			fee_result = distance_result * 4;
		else
			fee_result = distance_result * 2;
endmodule
