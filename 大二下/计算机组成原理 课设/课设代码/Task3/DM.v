// 数据存储器，实现lw/sw，lb/sb
module DM(
	input [13:0] addr,
	input [31:0] din,
	input we, clk,
	input islb, issb,
	output [31:0] dout
);
	reg [7:0] dm [12287:0];

	wire [7:0] lb_data = dm[addr];
	assign dout = islb ? {{24{lb_data[7]}}, lb_data} : {dm[addr+3], dm[addr+2], dm[addr+1], dm[addr]};
	// 小端序，输出

	integer i;
	initial
		begin
			for (i = 0; i < 4999; i = i + 1) 
				dm[i] <= 8'b0;
			for (i = 4999; i < 9998; i = i + 1) 
				dm[i] <= 8'b0;
			for (i = 9998; i < 12288; i = i + 1) 
				dm[i] <= 8'b0;
		end

	always @ (posedge clk)
		if (we)
			begin
				if (issb) 
					dm[addr] <= din[7:0];
				else 
					// 拼接，读取值
					{dm[addr+3], dm[addr+2], dm[addr+1], dm[addr]} <= din; 
			end

endmodule