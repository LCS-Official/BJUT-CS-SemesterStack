// `timescale 定义了仿真时间和精度
`timescale 1ns / 1ps

// 包含操作码定义，这样我们就可以使用 `ALU_ADD 等宏
`include "defines.v"

// Testbench 模块没有输入输出端口
module test_alu_tb;

    // 1. 信号声明
    // reg 类型用于向 DUT 提供激励输入
    reg  [31:0] tb_A;
    reg  [31:0] tb_B;
    reg  [3:0]  tb_ALUOp;

    // wire 类型用于从 DUT 接收结果输出
    wire [31:0] tb_Result;
    wire        tb_Zero;
    wire        tb_Overflow;


    // 2. 实例化你的 ALU 设计 (DUT)
    alu uut (
        .A(tb_A),
        .B(tb_B),
        .ALUOp(tb_ALUOp),
        .Result(tb_Result),
        .Zero(tb_Zero),
        .Overflow(tb_Overflow)
    );


    // 3. 编写测试激励序列
    initial begin
        $display("\n------ ALU Simulation Start ------");

        // --- 测试 ADD (addu) ---
        $display("\n[Test] ADD: 5 + 10");
        tb_A = 32'd5;
        tb_B = 32'd10;
        tb_ALUOp = `ALU_ADD;
        #10; // 等待10ns

        // --- 测试 SUB (subu) ---
        $display("\n[Test] SUB (non-zero): 20 - 15");
        tb_A = 32'd20;
        tb_B = 32'd15;
        tb_ALUOp = `ALU_SUB;
        #10;

        // --- 测试 SUB (zero), 验证 Zero 标志位 ---
        $display("\n[Test] SUB (zero): 100 - 100");
        tb_A = 32'd100;
        tb_B = 32'd100;
        tb_ALUOp = `ALU_SUB;
        #10;

        // --- 测试 OR (ori) ---
        $display("\n[Test] OR: 0x0000FFFF | 0xFFFF0000");
        tb_A = 32'h0000FFFF;
        tb_B = 32'hFFFF0000;
        tb_ALUOp = `ALU_OR;
        #10;
        
        // --- 测试 SLT (有符号小于) ---
        $display("\n[Test] SLT (true): -1 < 1");
        tb_A = -32'd1; // -1
        tb_B = 32'd1;  //  1
        tb_ALUOp = `ALU_SLT;
        #10;

        $display("\n[Test] SLT (false): 5 < -2");
        tb_A = 32'd5;
        tb_B = -32'd2;
        tb_ALUOp = `ALU_SLT;
        #10;

        // --- 测试 ADDI (带溢出检测) ---
        $display("\n[Test] ADDI (no overflow): 1000 + 2000");
        tb_A = 32'd1000;
        tb_B = 32'd2000;
        tb_ALUOp = `ALU_ADDI;
        #10;

        $display("\n[Test] ADDI (positive overflow): 0x7FFFFFFF + 1");
        tb_A = 32'h7FFFFFFF; // 最大的正数
        tb_B = 32'd1;
        tb_ALUOp = `ALU_ADDI;
        #10;

        $display("\n[Test] ADDI (negative overflow): 0x80000000 + (-1)");
        tb_A = 32'h80000000; // 最小的负数
        tb_B = -32'd1;       // -1
        tb_ALUOp = `ALU_ADDI;
        #10;

        $display("\n------ ALU Simulation End ------");
        $finish; // 结束仿真
    end


    // 4. 使用 $monitor 实时监控信号变化
    // 这会在任何一个被监控的信号发生变化时，自动打印一行信息
    initial begin
        $monitor("Time=%0t | A=%d, B=%d, ALUOp=%b | Result=%d, Zero=%b, Overflow=%b",
                 $time, tb_A, tb_B, tb_ALUOp, tb_Result, tb_Zero, tb_Overflow);
    end

endmodule