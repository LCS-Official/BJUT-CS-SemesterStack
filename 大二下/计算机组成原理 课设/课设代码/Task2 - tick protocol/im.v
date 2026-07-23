// im.v 
module im(
    input [31:0] addr,
    output [31:0] instr
);
    // 1KB = 1024 Bytes. Physical memory indices are [0:1023].
    reg [7:0] mem [0:1023];

    // 定义 MIPS 逻辑地址空间的基地址
    localparam BASE_ADDR = 32'h0000_3000;
    
    // 计算物理地址偏移量
    wire [11:0] physical_addr_offset;
    assign physical_addr_offset = addr - BASE_ADDR;

    initial begin
        // 请确保仿真时能找到这个 code.txt 文件
        $readmemh("code.txt", mem);
    end
    
    // 大端序拼接：
    // 低地址(mem[offset+0])的字节是指令的最高位字节。
    // 高地址(mem[offset+3])的字节是指令的最低位字节。
    assign instr = {mem[physical_addr_offset],   mem[physical_addr_offset+1], 
                    mem[physical_addr_offset+2], mem[physical_addr_offset+3]};

endmodule