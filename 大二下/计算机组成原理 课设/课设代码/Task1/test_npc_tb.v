// `timescale 定义了仿真时间和精度
`timescale 1ns / 1ps

// 包含宏定义
`include "defines.v"

// Testbench 模块没有输入输出端口
module test_npc_tb;

    // 1. 信号声明
    reg  [31:0] tb_PC;
    reg  [31:0] tb_SignImm;
    reg  [25:0] tb_Instr_25_0;
    reg  [31:0] tb_JR_Addr;
    reg  [1:0]  tb_PCSrc;

    wire [31:0] tb_NPC;


    // 2. 实例化你的 NPC 设计 (DUT)
    npc uut (
        .PC(tb_PC),
        .SignImm(tb_SignImm),
        .Instr_25_0(tb_Instr_25_0),
        .JR_Addr(tb_JR_Addr),
        .PCSrc(tb_PCSrc),
        .NPC(tb_NPC)
    );


    // 3. 编写测试激励序列
    initial begin
        $display("\n------ NPC Simulation Start ------");

        // 初始化所有输入
        tb_PC         = 32'b0;
        tb_SignImm    = 32'b0;
        tb_Instr_25_0 = 26'b0;
        tb_JR_Addr    = 32'b0;
        tb_PCSrc      = `PC_SRC_P4;

        // --- 测试 1: PC + 4 ---
        $display("\n[Test 1] PC Source = PC + 4");
        tb_PCSrc = `PC_SRC_P4;
        tb_PC    = 32'h00003000;
        #10; // 预期 NPC = 0x00003004

        // --- 测试 2: 分支目标地址 (beq) ---
        $display("\n[Test 2] PC Source = Branch Target");
        tb_PCSrc = `PC_SRC_BRANCH;
        tb_PC    = 32'h00003004;
        tb_SignImm = 32'sd10; // 立即数为10，跳转到 PC+4+40 的位置
        #10; // 预期 NPC = 0x3004 + 4 + (10<<2) = 0x3008 + 40 = 0x3030

        // --- 测试 3: 跳转目标地址 (j, jal) ---
        $display("\n[Test 3] PC Source = Jump Target");
        tb_PCSrc = `PC_SRC_JUMP;
        tb_PC    = 32'hA0001000; // PC高四位为'A'
        tb_Instr_25_0 = 26'h0100004; // 指令的低26位
        #10; // 预期 NPC = {0xA, 0x0100004, 0b00} = 0xA0400010

        // --- 测试 4: 寄存器跳转地址 (jr) ---
        $display("\n[Test 4] PC Source = Jump Register");
        tb_PCSrc = `PC_SRC_JR;
        tb_JR_Addr = 32'h12345678;
        #10; // 预期 NPC = 0x12345678

        $display("\n------ NPC Simulation End ------");
        $finish; // 结束仿真
    end

    // 4. 使用 $monitor 实时监控信号变化
    initial begin
        $monitor("Time=%0t | PCSrc=%b, PC=%h | NPC=%h",
                 $time, tb_PCSrc, tb_PC, tb_NPC);
    end

endmodule