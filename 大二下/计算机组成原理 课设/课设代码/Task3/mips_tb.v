`timescale 1ms/1ns

module mips_tb;

    reg         clk;
    reg         rst;
    reg  [31:0] dev1_rd;
    wire [31:0] Data2out;
    wire [31:0] cnt;
    wire        IntReq;
    integer     i;

    mips uut (
        .clk      (clk),
        .rst      (rst),
        .dev1_rd  (dev1_rd),
        .Data2out (Data2out),
        .IntReq   (IntReq),
        .cnt      (cnt)
    );

    // ------------------------------------------------------------
    // 时钟：周期 100 ns（10 MHz）
    // ------------------------------------------------------------
    initial begin
        clk = 0;
        forever #50 clk = ~clk;
    end

    // ------------------------------------------------------------
    // 测试激励
    // ------------------------------------------------------------
    initial begin
        dev1_rd = 32'h0000_1111;
        rst     = 1;
        #100 rst = 0;

        #100_000;
        dev1_rd = 32'h1111_0000;

        #100_000;

        $display("----- GPR -----");
        for (i = 0; i < 32; i = i + 1)
            $display("GPR[%0d] = 0x%08h", i, uut.GPR.registers[i]);

        $finish;
    end

    // ------------------------------------------------------------
    // 每个负边沿打印 CP0
    // ------------------------------------------------------------
    always @(negedge clk) begin
        $display("----- CP0 Registers -----");
        $display("SR   : 0x%08h", uut.CP0.rf_cp0[12]);
        $display("CAUSE: 0x%08h", uut.CP0.rf_cp0[13]);
        $display("EPC  : 0x%08h", uut.CP0.rf_cp0[14]);
        $display("PRID : 0x%08h", uut.CP0.rf_cp0[15]);
    end

endmodule
