/*
 * 模块名称: im_1k (Instruction Memory 1KB)
 * 文件名称: im_1k.v
 * 它负责存储MIPS指令，并根据给定的地址提供32位的指令。
 */
module im_1k(addr, dout);
  input [9:0]addr;
  output [31:0]dout;
  reg [7:0]im[1023:0] ;
  initial begin
		$readmemh("code.txt",im);
  end
  assign dout = {im[addr[9:0]], im[addr[9:0]+1], im[addr[9:0]+2], im[addr[9:0]+3]}; // 大端序
endmodule
