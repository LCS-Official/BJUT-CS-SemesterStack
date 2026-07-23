/*
 * 模块名称: dm (Data Memory 1KB)
 * 文件名称: dm.v
 * 描述:     MIPS数据存储器。
 * - 容量为1KB，内部由8位寄存器数组构成。
 * - 采用小端序方式存取数据。
 * - 写操作为同步，读操作为异步。
 * - 增加了rst端口，用于将所有内存单元异步复位清零。
 */
module dm(
    input         clk,       // 时钟信号
    input         rst,       // 复位信号
    input         we,        // 写使能
    input  [9:0]  addr,      // 10位地址
    input  [31:0] din,       // 待写入的32位数据
    output [31:0] dout       // 读出的32位数据
);

    // 内部存储结构：1KB，由1024个8位寄存器组成。
    reg [7:0] dm[1023:0];

    // 增加 for 循环所需的 integer 变量
    integer i;

    // 读操作 (异步/组合逻辑)
    assign dout = {dm[addr+3], dm[addr+2], dm[addr+1], dm[addr]};

    // 写操作 (同步/时序逻辑)
    // always块的敏感列表增加了 rst，并加入了复位逻辑
    always @(posedge clk or posedge rst) begin
        // 复位逻辑优先
        if (rst) begin
            // 当复位信号有效时，将所有1024个内存单元清零
            for (i = 0; i < 1024; i = i + 1) begin
                dm[i] <= 8'b0;
            end
        end 
        // 正常写操作逻辑
        else if (we) begin
            // 根据小端序规则，将32位输入数据拆分并存入4个连续的8位内存单元。
            dm[addr]   <= din[7:0];
            dm[addr+1] <= din[15:8];
            dm[addr+2] <= din[23:16];
            dm[addr+3] <= din[31:24];
        end
    end

endmodule