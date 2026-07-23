module distance_1015(
    input [4:0] dis_in,  					 // 5位输入（最大值为十进制25）     
    output reg [7:0] distance_result,   // 结果输出
	 output reg [7:0] fee_result         // 金额输出
);

    always @(*) begin
        distance_result = dis_in;  		 // 输出输入的距离
		  fee_result = distance_result * 10;  // 乘以10并保存
    end
endmodule
