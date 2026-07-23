/*
 * 模块名称: gpr (General Purpose Registers)
 * 文件名称: gpr.v
 * 描述:     MIPS通用寄存器堆。(带可综合的异步复位和用于仿真的监控代码)
 */
module gpr (
    // 端口列表
    input         clk,
    input         rst,
    input         RegWrite,
    input  [4:0]  A1,
    input  [4:0]  A2,
    input  [4:0]  A3,
    input  [31:0] WD3,
    output [31:0] RD1,
    output [31:0] RD2
);

    //-----------------------------------------------------//
    //------------ 1. 可综合的硬件设计部分 ------------//
    //-----------------------------------------------------//

    // 内部存储结构
    reg [31:0] registers[31:0];
    integer i;

    // 异步读操作
    assign RD1 = (A1 == 5'b0) ? 32'b0 : registers[A1];
    assign RD2 = (A2 == 5'b0) ? 32'b0 : registers[A2];

    // 带异步复位的同步写操作
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            for (i = 0; i < 32; i = i + 1) begin
                registers[i] <= 32'b0;
            end
        end 
        else if (RegWrite && (A3 != 5'b0)) begin
            registers[A3] <= WD3;
        end
    end


    //-----------------------------------------------------//
    //---------- 2. 仅用于仿真的监控代码部分 ----------//
    //-----------------------------------------------------//
    
    // 使用条件编译指令 `ifndef` (if not defined)
    // 只有在 "SYNTHESIS" 这个宏没有被定义时 (通常在仿真时)，
    // 下面的代码才会被编译器包含进去。
`ifndef SYNTHESIS
    always @(posedge clk) begin
        // 在每个时钟周期，如果发生了写操作，就打印信息
        if (RegWrite && (A3 != 5'd0)) begin
            // 使用 $time 系统函数来获取当前仿真时间
            $display("[GPR MONITOR] Time=%0t ns | Write to $%d with Data=0x%h", $time, A3, WD3);
        end
    end
`endif // 结束条件编译块

endmodule