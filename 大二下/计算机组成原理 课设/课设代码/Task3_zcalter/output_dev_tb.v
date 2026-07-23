// =================================================================================
// Testbench for: output_dev
// Description:   This testbench verifies the functionality of the output_dev
//                module, including reset, register writing, and register reading.
// =================================================================================
`timescale 1ns/1ps

module output_dev_tb;

    // --------------------------------------------------------------------------
    // 1. Signal and Parameter Declarations
    // --------------------------------------------------------------------------

    // -- Testbench-driven signals (Inputs to DUT) --
    reg           clk;
    reg           rst;
    reg           en;
    reg  [3:0]    addr;
    reg  [31:0]   din;

    // -- Monitored signals (Outputs from DUT) --
    wire [31:0]   dout;

    // -- Test Parameters for clarity --
    parameter ADDR_PRE_DATA = 4'b1000;
    parameter ADDR_CUR_DATA = 4'b1001;
    parameter ADDR_INVALID  = 4'b0000;
    
    parameter DATA_A = 32'hAAAAAAAA;
    parameter DATA_B = 32'hBBBBBBBB;

    // --------------------------------------------------------------------------
    // 2. Instantiate the Device Under Test (DUT)
    // --------------------------------------------------------------------------
    
    output_dev dut (
        .clk    (clk),
        .rst    (rst),
        .en     (en),
        .addr   (addr),
        .din    (din),
        .dout   (dout)
    );

    // --------------------------------------------------------------------------
    // 3. Clock Generation
    // --------------------------------------------------------------------------
    
    // Generate a clock with a 10ns period
    initial clk = 0;
    always #5 clk = ~clk;

    // --------------------------------------------------------------------------
    // 4. Test Sequence
    // --------------------------------------------------------------------------
    
    initial begin
        $display("--------------------------------------------------");
        $display("--- Starting output_dev Testbench ---");
        $display("--------------------------------------------------");

        // -- Test Case 1: Reset Test --
        $display("\n[TC1] Testing Reset...");
        rst = 1'b1; // Assert reset
        #15;        // Hold reset for more than one clock cycle
        rst = 1'b0; // De-assert reset
        #1;         // Wait a moment for logic to settle
        
        // Check internal registers after reset. This requires hierarchical reference.
        if (dut.preData === 32'h0 && dut.curData === 32'h0)
            $display("--> [PASS] Registers correctly cleared to 0 on reset.");
        else
            $display("--> [FAIL] Registers not cleared on reset. preData=%h, curData=%h", dut.preData, dut.curData);
        @(posedge clk);

        // -- Test Case 2: Write to preData register --
        $display("\n[TC2] Testing Write to preData register...");
        en   = 1'b1;
        addr = ADDR_PRE_DATA;
        din  = DATA_A;
        @(posedge clk); // Wait for the clock edge for the write to occur
        #1;
        if (dut.preData === DATA_A)
            $display("--> [PASS] preData correctly updated to %h.", DATA_A);
        else
            $display("--> [FAIL] preData was not updated correctly. Got %h", dut.preData);
        en = 1'b0; // End write cycle
        @(posedge clk);

        // -- Test Case 3: Write to curData register --
        $display("\n[TC3] Testing Write to curData register...");
        en   = 1'b1;
        addr = ADDR_CUR_DATA;
        din  = DATA_B;
        @(posedge clk);
        #1;
        if (dut.curData === DATA_B)
            $display("--> [PASS] curData correctly updated to %h.", DATA_B);
        else
            $display("--> [FAIL] curData was not updated correctly. Got %h", dut.curData);
        en = 1'b0;
        @(posedge clk);

        // -- Test Case 4: Read from preData register --
        $display("\n[TC4] Testing Read from preData register...");
        addr = ADDR_PRE_DATA;
        #1; // Wait for combinational read logic to update
        if (dout === DATA_A)
            $display("--> [PASS] Correctly read %h from preData.", DATA_A);
        else
            $display("--> [FAIL] Incorrect data read from preData. Got %h", dout);
        @(posedge clk);

        // -- Test Case 5: Read from curData register --
        $display("\n[TC5] Testing Read from curData register...");
        addr = ADDR_CUR_DATA;
        #1;
        if (dout === DATA_B)
            $display("--> [PASS] Correctly read %h from curData.", DATA_B);
        else
            $display("--> [FAIL] Incorrect data read from curData. Got %h", dout);
        @(posedge clk);

        // -- Test Case 6: Read from invalid address --
        $display("\n[TC6] Testing Read from invalid address...");
        addr = ADDR_INVALID;
        #1;
        if (dout === 32'bz)
            $display("--> [PASS] Correctly output high-impedance (Z).");
        else
            $display("--> [FAIL] Expected high-Z but got %h", dout);
        @(posedge clk);

        $display("\n--------------------------------------------------");
        $display("--- Testbench Finished ---");
        $display("--------------------------------------------------");
        $finish;
    end

endmodule