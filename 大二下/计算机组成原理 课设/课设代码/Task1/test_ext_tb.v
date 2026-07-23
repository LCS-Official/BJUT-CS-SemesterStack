// `timescale 定义了仿真时间和精度
`timescale 1ns / 1ps

// Testbench 模块没有输入输出端口
module test_ext_tb;

    // 1. 信号声明
    // reg 类型用于向 DUT 提供激励输入
    reg  [15:0] tb_Imm16;
    reg         tb_ExtOp;

    // wire 类型用于从 DUT 接收结果输出
    wire [31:0] tb_Imm32;


    // 2. 实例化你的 EXT 设计 (DUT)
    ext uut (
        .Imm16(tb_Imm16),
        .ExtOp(tb_ExtOp),
        .Imm32(tb_Imm32)
    );


    // 3. 编写测试激励序列
    initial begin
        $display("\n------ EXT Simulation Start ------");

        // --- 测试 1: 符号扩展一个负数 (最高位为1) ---
        $display("\n[Test 1] Sign Extend a negative number (0x8A2B)");
        tb_ExtOp = 1'b1; // 1: 代表符号扩展
        tb_Imm16 = 16'h8A2B;
        #10; // 等待10ns
        // 预期结果: 0xFFFF8A2B

        // --- 测试 2: 符号扩展一个正数 (最高位为0) ---
        $display("\n[Test 2] Sign Extend a positive number (0x7A2B)");
        tb_ExtOp = 1'b1;
        tb_Imm16 = 16'h7A2B;
        #10;
        // 预期结果: 0x00007A2B

        // --- 测试 3: 零扩展一个负数 (最高位为1) ---
        $display("\n[Test 3] Zero Extend a negative number (0x8A2B)");
        tb_ExtOp = 1'b0; // 0: 代表零扩展
        tb_Imm16 = 16'h8A2B;
        #10;
        // 预期结果: 0x00008A2B

        // --- 测试 4: 零扩展一个正数 (最高位为0) ---
        $display("\n[Test 4] Zero Extend a positive number (0x7A2B)");
        tb_ExtOp = 1'b0;
        tb_Imm16 = 16'h7A2B;
        #10;
        // 预期结果: 0x00007A2B

        $display("\n------ EXT Simulation End ------");
        $finish; // 结束仿真
    end


    // 4. 使用 $monitor 实时监控信号变化
    initial begin
        $monitor("Time=%0t | ExtOp=%b, Imm16=%h | Imm32=%h",
                 $time, tb_ExtOp, tb_Imm16, tb_Imm32);
    end

endmodule