// =================================================================================
// Testbench for: timer (Unit Test)
// Description:   This testbench verifies the core functionality of the timer module.
//                It tests reset, configuration writing, countdown process,
//                and interrupt signal generation.
// =================================================================================
`timescale 1ns/1ps

module timer_tb;

    // --------------------------------------------------------------------------
    // 1. Signal Declarations
    // --------------------------------------------------------------------------
    
    // -- Inputs to the timer (driven by this testbench) --
    reg           clk;
    reg           rst;
    reg  [3:0]    addr;
    reg           Wr_en;
    reg  [31:0]   data_in;
    reg           alt_sign; // Signal to make the counter decrement

    // -- Outputs from the timer (to be monitored) --
    wire          pause_q;  // The interrupt request signal

    // --------------------------------------------------------------------------
    // 2. Instantiate the Device Under Test (DUT)
    // --------------------------------------------------------------------------
    
    // We assume the corrected version of the timer is being used.
    timer dut (
        .clk        (clk),
        .rst        (rst),
        .addr       (addr),
        .Wr_en      (Wr_en),
        .data_in    (data_in),
        .pause_q    (pause_q),
        .alt_sign   (alt_sign)
    );

    // --------------------------------------------------------------------------
    // 3. Clock Generation
    // --------------------------------------------------------------------------
    
    initial clk = 0;
    always #5 clk = ~clk; // 10ns clock period

    // --------------------------------------------------------------------------
    // 4. Test Sequence
    // --------------------------------------------------------------------------
    
    // Task to simulate a single write cycle from the CPU
    task write_timer;
        input [3:0]  i_addr;
        input [31:0] i_data;
        begin
            @(posedge clk);
            Wr_en   = 1'b1;
            addr    = i_addr;
            data_in = i_data;
            @(posedge clk);
            Wr_en   = 1'b0;
        end
    endtask

    initial begin
        $display("-----------------------------------");
        $display("--- Starting Timer Unit Test ---");
        $display("-----------------------------------");

        // -- Initialization & Reset Test --
        $display("\n[TC1] Testing Reset...");
        rst      = 1'b1;
        Wr_en    = 1'b0;
        alt_sign = 1'b0;
        addr     = 4'h0;
        data_in  = 32'h0;
        #20;
        rst = 1'b0;
        #1;
        if (dut.cnt_reg === 32'h0)
            $display("--> [PASS] Counter correctly cleared to 0 on reset.");
        else
            $display("--> [FAIL] Counter not cleared on reset. Got %d", dut.cnt_reg);
        
        // --- Test Case 2: Configure and Start the Timer ---
        $display("\n[TC2] Configuring timer for a countdown of 5 ticks...");
        // Write to Control Register (addr=0): Mode=0, Interrupt Enable=1, Timer Enable=1
        // ctrl_sign[3]=1 (pause_acc), ctrl_sign[2:1]=00 (mode_sel), ctrl_sign[0]=1 (enable)
        // Corresponds to value: 0...1001 = 9
        write_timer(4'h0, 32'h9); 
        
        // Write to Initial Value Register (addr=1) with a value of 5
        write_timer(4'h1, 32'd5);
        #1;
        
        if (dut.cnt_reg === 32'd5)
            $display("--> [PASS] cnt_reg correctly loaded with value 5.");
        else
            $display("--> [FAIL] cnt_reg failed to load. Got %d", dut.cnt_reg);

        // --- Test Case 3: Countdown and Interrupt Check ---
        $display("\n[TC3] Waiting for countdown to finish and interrupt to fire...");
        // Let the timer count down for 5 ticks
			alt_sign = 1'b1; // 在倒计时期间，保持节拍信号一直有效
			repeat (5) begin
				 @(posedge clk); // 等待5个时钟周期，这样每个周期cnt_reg都会减1
			end
			alt_sign = 1'b0; // 倒计时结束后可以关闭

        @(posedge clk); // One more clock for the interrupt signal to propagate
        #1;

        if (dut.cnt_reg === 32'h0 && pause_q === 1'b1)
            $display("--> [PASS] Countdown finished and interrupt (pause_q) is correctly asserted!");
        else
            $display("--> [FAIL] Countdown/Interrupt error. cnt_reg=%d, pause_q=%b", dut.cnt_reg, pause_q);
        
        // --- Test Case 4: Check post-interrupt behavior ---
        $display("\n[TC4] Checking if timer stops after interrupt (Mode 0)...");
        @(posedge clk);
        alt_sign = ~alt_sign;
        #1;
        if (dut.cnt_reg === 32'h0) // Assuming corrected logic where it stops at 0
            $display("--> [PASS] Counter correctly stopped at 0 after firing.");
        else
            $display("--> [FAIL] Counter did not stop after firing. cnt_reg=%d", dut.cnt_reg);


        $display("\n-----------------------------------");
        $display("--- Timer Testbench Finished ---");
        $display("-----------------------------------");
        $finish;
    end

endmodule