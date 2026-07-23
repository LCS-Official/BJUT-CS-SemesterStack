`timescale 1ns/1ps

module test_mips_tb;

    // 1. 信号声明
    reg clk;
    reg rst;

    // 2. 实例化顶层 MIPS 模块
    mips my_mips (
        .clk(clk),
        .rst(rst)
    );

    // 3. 时钟生成（10ns周期）
    initial clk = 0;
    always #5 clk = ~clk;

    // 4. 初始化、运行与监控
    initial begin
        $display("\n------ MIPS CPU Run-to-Completion Test Start ------");

        // 复位处理器
        rst = 1;
        #20; // 保持复位20ns
        rst = 0;
        $display("Reset released. Processor running...");

        // 运行一个足够长的固定时间，以确保程序跑完
        #20000;

        $display("\n------ Test Finished ------");
        $finish; // 自动结束仿真
    end

endmodule