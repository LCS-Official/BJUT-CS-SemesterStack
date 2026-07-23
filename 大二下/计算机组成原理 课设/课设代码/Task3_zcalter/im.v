module im_1k(addr, dout);
	input [9:0] addr;
	output [31:0] dout;
	 
	reg [7:0] im[8191:0];
	 
	// 小端序
	assign dout = {im[addr], im[addr+1], im[addr+2], im[addr+3]};
    
endmodule