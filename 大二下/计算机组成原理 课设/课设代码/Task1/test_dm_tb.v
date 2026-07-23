// `timescale 定义了仿真时间和精度
`timescale 1ns / 1ps

// Testbench 模块没有输入输出端口
module test_dm_tb;

    // 1. 信号声明
    // reg 类型用于向 DUT 提供激励输入
    reg         clk;
    reg         we;
    reg  [9:0]  tb_addr;
    reg  [31:0] tb_din;

    // wire 类型用于从 DUT 接收结果输出
    wire [31:0] tb_dout;


    // 2. 实例化你的 DM 设计 (DUT)
    // 使用你指定的模块名 dm
    dm uut (
        .clk(clk),
        .we(we),
        .addr(tb_addr),
        .din(tb_din),
        .dout(tb_dout)
    );


    // 3. 时钟生成
    // 使用 always 块生成一个周期为10ns的时钟信号
    initial clk = 0;
    always #5 clk = ~clk;


    // 4. 编写测试激励序列
    initial begin
        $display("\n------ DM Simulation Start ------");

        // 初始化所有输入
        we = 0;
        tb_addr = 10'd0;
        tb_din = 32'b0;
        
        // --- 测试1: 小端序写入与读取 ---
        $display("\n[Test 1] Writing 0x11223344 to address 100 (Little-Endian)...");
        @(posedge clk); // 等待下一个时钟上升沿
        we = 1;
        tb_addr = 10'd100;
        tb_din = 32'h11223344;
        
        @(posedge clk); // 数据已在此时钟沿写入
        $display("         Write operation finished. Verifying readback...");
        we = 0; // 关闭写使能，防止意外写入
        #1; // 等待1ns，让组合逻辑的读输出稳定显示
        // 此时读地址仍是100，观察 tb_dout 是否为 0x11223344

        // --- 测试2: 验证写使能(we)信号 ---
        $display("\n[Test 2] Attempting to write 0xDEADBEEF to addr 200 with we=0...");
        tb_addr = 10'd200;
        tb_din = 32'hDEADBEEF;
        // we 保持为0
        @(posedge clk);
        
        #1; // 稳定一下
        $display("         Verifying write was blocked...");
        // 此时读地址是200，观察 tb_dout 是否为 xxxxxxxx (未初始化)

        // --- 测试3: 验证异步读 ---
        $display("\n[Test 3] Testing asynchronous read by switching address back to 100...");
        tb_addr = 10'd100; // 不等待时钟，立即改变地址
        #1; // 稳定一下，观察 tb_dout 是否立即变回 0x11223344

        $display("\n------ DM Simulation End ------");
        $finish; // 结束仿真
    end


    // 5. 使用 $monitor 实时监控信号变化
    initial begin
        $monitor("Time=%0t | WE=%b Addr=%d Din=%h | Dout=%h",
                 $time, we, tb_addr, tb_din, tb_dout);
    end

endmodule