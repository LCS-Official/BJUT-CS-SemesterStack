`timescale 1ns/1ps

module mips_tb;

    // 1. 信号声明
    reg clk;
    reg rst;

    // 2. 实例化您的顶层 MIPS 模块
    mips uut (
        .clk(clk),
        .rst(rst)
    );

    // 3. 时钟生成 (10ns 周期 -> 100MHz)
    initial begin
        clk = 0;
    end
    always #5 clk = ~clk;

    // 4. 运行控制
    initial begin
        // 产生一个复位脉冲
        rst = 1;
        #20; // 保持复位 20ns
        rst = 0;

        // 持续运行一段时间以产生足够长的波形供分析
        // 例如，5000ns (500个时钟周期)
        #5000;

        // 运行指定时间后，自动结束仿真
        // 这样 `run -all` 才能跑完并停止
        $finish;
    end

endmodule