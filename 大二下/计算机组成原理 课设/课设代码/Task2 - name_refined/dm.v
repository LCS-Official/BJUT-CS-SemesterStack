/*
 * 模块名称: dm (Data Memory 1KB)
 * 文件名称: dm.v
 * 描述:     MIPS数据存储器。
 * - 容量为1KB，内部由8位寄存器数组构成。
 * - 采用小端序方式存取数据。
 * - 写操作为同步，读操作为异步。
 * - 增加了rst端口，用于将所有内存单元异步复位清零。
 */

module dm(addr, din, we, clk, dout, lb_en, sb_en);//实现相应的数据存储器的写入及输出功能。
	input [9:0]addr;  //数据存储器地址
	input [31:0]din;  //addr处数据的输入
	input we;    //写使能
	input clk;
	input lb_en;
	input sb_en;
	output [31:0]dout;  // 输出数据
	reg [7:0] dm[1023:0]; // 存储体
  
	wire [9:0]tmp = addr[9:0];
  
	integer i = 0;
  
	initial begin
		for (i = 0; i < 1024; i = i + 1)
			dm[i] = 8'b0;
	end
  
	always @ (posedge clk) begin				//实现相应的数据存储器的写入
		if (we) begin
			if (sb_en) begin
				dm[tmp] = din[7:0];
			end
			else begin
				dm[tmp] = din[7:0];
				dm[tmp + 1] = din[15:8];
				dm[tmp + 2] = din[23:16];
				dm[tmp + 3] = din[31:24];
			end
		end
	end
	assign dout = (lb_en)? {{24{dm[tmp][7]}},dm[tmp]} : {dm[tmp+3], dm[tmp+2], dm[tmp+1], dm[tmp]};   //根据输入的地址，将输入的数据写入相应的寄存器
  
endmodule
