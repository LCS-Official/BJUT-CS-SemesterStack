`timescale 1ns/1ps

// Testbench for testing foundational instructions (ALU, MEM, BRANCH)
// It checks the final register values against expected results.

module mips_tb;


    // 1. 信号声明
    reg clk;
    reg rst;

    // 2. 实例化顶层 MIPS 模块
    mips uut (
        .clk(clk),
        .rst(rst)
    );

    // 3. 时钟生成
    initial clk = 0;
    always #5 clk = ~clk;

    // 4. 初始化与运行控制
    initial begin
        $display("\n------ Memory and Branch Instruction Test Start ------");

        rst = 1;
        #20;
        rst = 0;

        // 运行 1000ns，足以完成此测试程序
        #1000;

        // 5. 打印最终寄存器快照以验证结果
        $display("\n-----------------------------------------------------");
        $display("------ Final Register State Check at %0t ns ------", $time);
        $display("-----------------------------------------------------");
        $display("Comparing RUNTIME value with EXPECTED value...");

        // 检查目标寄存器值
        // 路径 uut.u_datapath.reg_file.rf 必须与您的设计层级和命名匹配
        $display("$t0 (R8) : 0x%08h (Expected: 0x0000abcd)", uut.u_datapath.reg_file.rf[8]);
        $display("$t1 (R9) : 0x%08h (Expected: 0x0000bbfd)", uut.u_datapath.reg_file.rf[9]);
        $display("$t2 (R10): 0x%08h (Expected: 0x0000abcd)", uut.u_datapath.reg_file.rf[10]);
        $display("$s1 (R17): 0x%08h (Expected: 0x00000001)", uut.u_datapath.reg_file.rf[17]);
        $display("$s2 (R18): 0x%08h (Expected: 0x00000003)", uut.u_datapath.reg_file.rf[18]);

        $display("-----------------------------------------------------");

        $display("\n------ Memory and Branch Instruction Test End ------");
        $finish; 
    end

endmodule