/*
 * 模块名称: im (Instruction Memory 1KB)
 * 文件名称: im.v
 * 描述:     此模块完全遵照《Project1 VerilogHDL完成单周期处理器开发》文档要求实现。
 * 它负责存储MIPS指令，并根据给定的地址提供32位的指令。
 */
module im(
    input   [9:0]  addr,
    output  [31:0] dout
);
    reg [7:0] im_mem[1023:0];

    initial begin
        $readmemh("code.txt", im_mem);
    end

    // 大端序拼接
    assign dout = {im_mem[addr], im_mem[addr+1], im_mem[addr+2], im_mem[addr+3]};
endmodule