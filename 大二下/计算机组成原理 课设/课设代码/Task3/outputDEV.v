module outputDEV(clk, en, addr, din, dout, Data_out);
	input clk, en;
	input [3:2] addr;	// 输入的寄存器地址
	input [31:0] din;
	output [31:0] dout;// 输出的读取数据，面向CPU
	output[31:0]Data_out;// 输出：连接到显示设备的数据
	reg [31:0] preData, curData;// 存储前后两次输入值的寄存器
	
	initial begin
		// 存两个data，双缓冲、方便软件进行比较或回溯
		preData = 0; curData = 0;
	end
  
	always @ (posedge clk)
		if(en)
			case(addr)
				// 00：更新前一次输入数据
				2'b00: preData <= din;
				// 01：更新当前输入数据
				2'b01: curData <= din;
				default:;
			endcase

	assign dout = (addr == 2'b00) ? preData : (addr == 2'b01) ? curData : 32'bz;
	assign Data_out = curData;
	
endmodule