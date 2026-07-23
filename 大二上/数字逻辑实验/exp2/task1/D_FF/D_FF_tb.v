`timescale 1ns / 1ps  // 设置时间单位和精度

module D_FF_tb;

    // Testbench 信号声明
    reg clk;
    reg D;
    wire Q;

    // 实例化待测模块 D_FF
    D_FF uut (
        .clk(clk),
        .D(D),
        .Q(Q)
    );

    // 生成时钟信号，每10ns切换一次，即20ns周期
    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end

    // 初始化和激励输入信号
    initial begin
        // 打印标题
        $display("Time\tclk\tD\tQ");

        // 应用输入信号的初始值
        D = 0;
        #15;  // 等待 15ns，让 Q 响应时钟的上升沿

        // 改变 D 的值并观察 Q 的响应
        D = 1;  #20;  // 在时钟的上升沿时，D 应该传到 Q
        D = 0;  #20;  // 另一个时钟上升沿，观察 D -> Q
        D = 1;  #20;
        D = 0;  #20;

        // 结束仿真
        #20 $finish;
    end

    // 打印波形变化
    initial begin
        $monitor("%g\t%b\t%b\t%b", $time, clk, D, Q);
    end

endmodule
