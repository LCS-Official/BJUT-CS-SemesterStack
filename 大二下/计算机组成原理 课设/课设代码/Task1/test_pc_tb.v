// `timescale 定义了仿真时间和精度
`timescale 1ns / 1ps

// Testbench 模块没有输入输出端口
module test_pc_tb;

    // 1. 信号声明
    reg         clk;
    reg         rst;
    reg  [31:0] tb_NPC;

    wire [31:0] tb_PC;


    // 2. 实例化你的 PC 设计 (DUT)
    pc uut (
        .clk(clk),
        .rst(rst),
        .NPC(tb_NPC),
        .PC(tb_PC)
    );


    // 3. 时钟生成
    initial clk = 0;
    always #5 clk = ~clk; // 周期为10ns的时钟


    // 4. 编写测试激励序列
    initial begin
        $display("\n------ PC Simulation Start ------");

        // --- 测试 1: 验证复位功能 ---
        $display("\n[Test 1] Asserting reset...");
        rst = 1'b1; // 拉高复位信号
        #15; // 持续一段时间，确保复位生效
        // 预期结果: tb_PC 应该为 0x0000_3000

        // --- 测试 2: 撤销复位，验证第一次加载 ---
        $display("\n[Test 2] De-asserting reset, loading first NPC value...");
        rst = 1'b0; // 撤销复位
        tb_NPC = 32'h0000_3004;
        @(posedge clk); // 等待一个时钟上升沿
        // 预期结果: tb_PC 应该更新为 0x0000_3004

        // --- 测试 3: 验证第二次加载 ---
        $display("\n[Test 3] Loading second NPC value...");
        tb_NPC = 32'h0000_3008;
        @(posedge clk);
        // 预期结果: tb_PC 应该更新为 0x0000_3008
        
        // --- 测试 4: 再次验证复位功能 ---
        $display("\n[Test 4] Re-asserting reset during operation...");
        rst = 1'b1;
        #15;
        // 预期结果: tb_PC 应该再次变回 0x0000_3000

        $display("\n------ PC Simulation End ------");
        $finish; // 结束仿真
    end

    // 5. 使用 $monitor 实时监控信号变化
    initial begin
        $monitor("Time=%0t | Rst=%b, NPC=%h | PC=%h",
                 $time, rst, tb_NPC, tb_PC);
    end

endmodule