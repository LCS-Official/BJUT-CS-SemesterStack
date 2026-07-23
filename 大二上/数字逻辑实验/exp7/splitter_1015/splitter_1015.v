module splitter_1015(
	input [7:0] vendingmachine_out,distance_out,change_out,fee_out,
	output reg [3:0] dis1,dis2,fee1,fee2,ven1,ven2,cha1,cha2
);
	
	always @(*) 
		begin
			dis1 = distance_out[7:4];  // 高4位
			dis2 = distance_out[3:0];  // 低4位

			fee1 = fee_out[7:4];       // 高4位
			fee2 = fee_out[3:0];       // 低4位

			ven1 = vendingmachine_out[7:4]; // 高4位
			ven2 = vendingmachine_out[3:0]; // 低4位

			cha1 = change_out[7:4];    // 高4位
			cha2 = change_out[3:0];    // 低4位
		end

endmodule