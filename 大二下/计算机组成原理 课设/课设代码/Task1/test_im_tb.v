// `timescale 定义了仿真时间和精度
`timescale 1ns / 1ps

// Testbench 模块通常是空的，没有输入输出端口
module test_im_tb;

    // 1. 信号声明
    // 要给 DUT 的输入端口连接的信号，声明为 reg 类型
    reg  [9:0]  tb_addr;

    // 从 DUT 的输出端口连接出来的信号，声明为 wire 类型
    wire [31:0] tb_dout;


    // 2. 实例化你的设计 (DUT)
    // 将我们上面声明的信号连接到 im_1k 模块的端口上
    im uut (
        .addr(tb_addr),  // im_1k 的 addr 端口连接到 tb_addr
        .dout(tb_dout)   // im_1k 的 dout 端口连接到 tb_dout
    );


    // 3. 编写测试激励 (Stimulus)
    // initial 块中的代码会在仿真开始时顺序执行
    initial begin
        // 使用 $display 可以在仿真控制台打印信息
        $display("------ Simulation Start: Testing im ------");

        // 测试地址 0
        tb_addr = 10'd0; // 10'd0 表示10位的十进制数0
        #10; // 延时 10ns，等待信号稳定和显示
        $display("Address = %h, Instruction = %h", tb_addr, tb_dout);

        // 测试地址 4
        tb_addr = 10'd4;
        #10;
        $display("Address = %h, Instruction = %h", tb_addr, tb_dout);
        
        // 测试地址 8
        tb_addr = 10'd8;
        #10;
        $display("Address = %h, Instruction = %h", tb_addr, tb_dout);

        // 结束仿真
        $display("------ Simulation End ------");
        $finish;
    end

endmodule