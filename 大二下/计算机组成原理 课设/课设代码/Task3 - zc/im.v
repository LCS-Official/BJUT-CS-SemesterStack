//same
module im_1k(addr, dout) ;
    input   [9:0]   addr ;//1k空间 10位地址 1024字节
    output  [31:0]  dout ;//指令地址处取出32位指令输出
    reg     [7:0]   im[8191:0] ;//指令寄存器 1024字节 每个字节8位
    assign dout = {im[addr], im[addr+1], im[addr+2], im[addr+3]};
    
endmodule