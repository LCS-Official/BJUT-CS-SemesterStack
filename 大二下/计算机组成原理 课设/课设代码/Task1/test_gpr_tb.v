// `timescale 定义了仿真时间和精度
`timescale 1ns / 1ps

// Testbench 模块没有输入输出端口
module test_gpr_tb;

    // 1. 信号声明
    // reg 类型用于向 DUT 提供激励输入
    reg         clk;
    reg         RegWrite;
    reg  [4:0]  tb_A1, tb_A2, tb_A3;
    reg  [31:0] tb_WD3;

    // wire 类型用于从 DUT 接收结果输出
    wire [31:0] tb_RD1, tb_RD2;


    // 2. 实例化你的 GPR 设计 (DUT)
    gpr uut (
        .clk(clk),
        .RegWrite(RegWrite),
        .A1(tb_A1),
        .A2(tb_A2),
        .A3(tb_A3),
        .WD3(tb_WD3),
        .RD1(tb_RD1),
        .RD2(tb_RD2)
    );


    // 3. 时钟生成
    // 使用 always 块生成一个周期为10ns的时钟信号
    initial clk = 0;
    always #5 clk = ~clk;


    // 4. 编写测试激励序列
    initial begin
        $display("\n------ GPR Simulation Start ------");

        // 初始化所有输入
        RegWrite = 0;
        tb_A1 = 5'b0;
        tb_A2 = 5'b0;
        tb_A3 = 5'b0;
        tb_WD3 = 32'b0;
        
        // --- 测试1: 向寄存器 $t0(8) 写入数据 ---
        $display("\n[Test 1] Writing 0xAAAAAAAA to register $t0(8)...");
        @(posedge clk); // 等待下一个时钟上升沿
        RegWrite = 1;
        tb_A3 = 5'd8;
        tb_WD3 = 32'hAAAAAAAA;
        
        // --- 测试2: 写入的同时，从 $t0(8) 和 $t1(9) 读取 ---
        // 读操作是异步的，应该能立即看到旧值（或x）。写操作将在下一个时钟沿生效。
        $display("[Test 2] Reading from $t0(8) and $t1(9) during write...");
        tb_A1 = 5'd8;
        tb_A2 = 5'd9;
        
        // --- 测试3: 验证写入是否成功 ---
        @(posedge clk); // 数据已在此时钟沿写入
        $display("[Test 3] Verifying write to $t0(8)...");
        RegWrite = 0; // 关闭写使能
        // 读地址已在上一周期设置好，现在观察 tb_RD1 的输出
        #1; // 等待1ns，让组合逻辑的输出稳定显示

        // --- 测试4: 尝试向 $0 写入数据 ---
        $display("\n[Test 4] Attempting to write 0xDEADBEEF to register $0...");
        @(posedge clk);
        RegWrite = 1;
        tb_A3 = 5'd0;
        tb_WD3 = 32'hDEADBEEF;

        // --- 测试5: 验证 $0 是否仍然为0 ---
        @(posedge clk);
        $display("[Test 5] Verifying register $0 is still zero...");
        RegWrite = 0;
        tb_A1 = 5'd0; // 读取 $0
        #1; // 等待输出稳定

        $display("\n------ GPR Simulation End ------");
        $finish; // 结束仿真
    end


    // 5. 使用 $monitor 实时监控信号变化
    initial begin
        $monitor("Time=%0t | WriteEnable=%b Addr(W/R1/R2)=%d/%d/%d WriteData=%h | ReadData1=%h ReadData2=%h",
                 $time, RegWrite, tb_A3, tb_A1, tb_A2, tb_WD3, tb_RD1, tb_RD2);
    end

endmodule