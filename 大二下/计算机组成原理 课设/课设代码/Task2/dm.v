/*
 * 模块名称: dm_1k (Data Memory 1KB)
 * 文件名称: dm.v
 * MIPS数据存储器。
 */
module dm_1k(addr, din, we, clk, dout, lben, sben);
  input [9:0]addr ;  //数据存储器地址
  input [31:0]din ;  //addr处数据的输入
  input we;    //写使能
  input clk;
  input lben;
  input sben;
  output [31:0]dout;  // 输出数据
  reg [7:0] dm[1023:0];
  
  wire [9:0]tmp = addr[9:0];
  
  integer i; // 后续用于遍历
  
  initial begin
    for (i = 0; i < 1024; i = i + 1)
      dm[i] = 8'b0;
  end
  
	always @ (posedge clk) begin
		 if (we) begin // 只有在写使能we有效时才执行
			  if (sben) begin // 如果是 "sb"
					dm[addr] = din[7:0]; // 只将输入数据的最低8位写入指定地址
			  end
			  else begin // 否则，认为是 "sw"
					dm[addr]     = din[7:0];   // 将32位数据拆分成4个字节
					dm[addr + 1] = din[15:8];  // 存入连续的4个地址中
					dm[addr + 2] = din[23:16];
					dm[addr + 3] = din[31:24];
			  end
		 end
	end
  assign dout = (lben)? {{24{dm[tmp][7]}},dm[tmp]} : {dm[tmp+3], dm[tmp+2], dm[tmp+1], dm[tmp]};  
  // 异步读、lw lb实现
  // lw从addr开始读取连续的4个字节，并按小端模式将它们拼接成一个32位的字 
  // lb采用符号位扩展，也就是把dm[addr]复制24次，拼接到字节前面，扩展成32位
endmodule
