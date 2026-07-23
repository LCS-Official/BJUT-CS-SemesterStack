// =================================================================================
// Testbench for: cp0 (System Control Coprocessor)
// Description:   Verifies reset, MTC0, MFC0, interrupt request generation,
//                and exception entry/return logic of the CP0 module.
// =================================================================================
`timescale 1ns/1ps

module cp0_tb;

    // --------------------------------------------------------------------------
    // 1. Signal and Parameter Declarations
    // --------------------------------------------------------------------------

    // -- Testbench-driven signals (Inputs to DUT) --
    reg           clk;
    reg           rst;
    reg  [31:0]   pcout;
    reg  [31:0]   rt_din;
    reg  [5:0]    HWInt;
    reg  [4:0]    Sel;
    reg           cp0wr;
    reg           EXLSet;
    reg           EXLClr;

    // -- Monitored signals (Outputs from DUT) --
    wire          IntReq;
    wire [31:0]   epc;
    wire [31:0]   cp0dout;
    
    // -- CP0 Register Addresses for convenience --
    localparam [4:0] ADDR_SR    = 5'd12;
    localparam [4:0] ADDR_CAUSE = 5'd13;
    localparam [4:0] ADDR_EPC   = 5'd14;
    localparam [4:0] ADDR_PRID  = 5'd15;

    // --------------------------------------------------------------------------
    // 2. Instantiate the Device Under Test (DUT)
    // --------------------------------------------------------------------------

    cp0 dut (
        .pcout    (pcout),
        .rt_din   (rt_din),
        .HWInt    (HWInt),
        .Sel      (Sel),
        .cp0wr    (cp0wr),
        .EXLSet   (EXLSet),
        .EXLClr   (EXLClr),
        .clk      (clk),
        .rst      (rst),
        .IntReq   (IntReq),
        .epc      (epc),
        .cp0dout  (cp0dout)
    );

    // --------------------------------------------------------------------------
    // 3. Clock Generation
    // --------------------------------------------------------------------------
    
    initial clk = 0;
    always #5 clk = ~clk;

    // --------------------------------------------------------------------------
    // 4. Test Sequence
    // --------------------------------------------------------------------------
    
    initial begin
        $display("-----------------------------------");
        $display("--- Starting CP0 Testbench ---");
        $display("-----------------------------------");

        // -- Initialization --
        pcout  = 32'h0;
        rt_din = 32'h0;
        HWInt  = 6'h0;
        Sel    = 5'h0;
        cp0wr  = 1'b0;
        EXLSet = 1'b0;
        EXLClr = 1'b0;

        // --- Test Case 1: Reset Test ---
        $display("\n[TC1] Testing Reset...");
        rst = 1'b1;
        #15;
        rst = 1'b0;
        #1;
        // Check a few key reset values. This requires hierarchical reference.
        if (dut.regarray_cp0[ADDR_SR] === 32'h0000_0401 && dut.regarray_cp0[ADDR_PRID] === 32'h2307_0215)
            $display("--> [PASS] Registers correctly initialized on reset.");
        else
            $display("--> [FAIL] Incorrect reset values.");
        @(posedge clk);

        // --- Test Case 2: MTC0 - Write to SR to disable interrupts ---
        $display("\n[TC2] Testing MTC0 to write SR...");
        Sel    = ADDR_SR;
        rt_din = 32'h0000_0400; // New value for SR: IM=1, but IE=0
        cp0wr  = 1'b1;
        @(posedge clk);
        #1;
        cp0wr = 1'b0;
        if (dut.regarray_cp0[ADDR_SR] === 32'h0000_0400)
            $display("--> [PASS] SR correctly written via MTC0.");
        else
            $display("--> [FAIL] SR write failed.");
        @(posedge clk);

        // --- Test Case 3: Interrupt Request Logic (should be blocked by IE=0) ---
        $display("\n[TC3] Testing IntReq (blocked by IE=0)...");
        HWInt = 6'b000001; // Assert lowest interrupt line
        #1;
        if (IntReq === 1'b0)
            $display("--> [PASS] IntReq correctly blocked by IE flag.");
        else
            $display("--> [FAIL] IntReq was not blocked by IE flag.");
        HWInt = 6'b0;
        @(posedge clk);
        
        // --- Test Case 4: Exception Entry (EXLSet) ---
        $display("\n[TC4] Testing Exception Entry (EXLSet)...");
        pcout = 32'h1234_ABCD; // Simulate the PC value to be saved
        EXLSet = 1'b1;
        @(posedge clk);
        #1;
        EXLSet = 1'b0;
        // Check if EPC was saved and EXL bit in SR is set
        if (dut.regarray_cp0[ADDR_EPC] === 32'h1234_ABCD && dut.regarray_cp0[ADDR_SR][1] === 1'b1)
             $display("--> [PASS] EPC saved and EXL set correctly.");
        else
             $display("--> [FAIL] Exception entry failed. EPC=%h, SR[1]=%b", dut.regarray_cp0[ADDR_EPC], dut.regarray_cp0[ADDR_SR][1]);
        @(posedge clk);

        // --- Test Case 5: MFC0 - Read from EPC ---
        $display("\n[TC5] Testing MFC0 to read EPC...");
        Sel = ADDR_EPC;
        #1;
        if (cp0dout === 32'h1234_ABCD)
            $display("--> [PASS] Correctly read EPC value via MFC0.");
        else
            $display("--> [FAIL] MFC0 read from EPC failed. Got %h", cp0dout);
        @(posedge clk);

        // --- Test Case 6: Exception Return (EXLClr) ---
        $display("\n[TC6] Testing Exception Return (EXLClr)...");
        EXLClr = 1'b1;
        @(posedge clk);
        #1;
        EXLClr = 1'b0;
        if (dut.regarray_cp0[ADDR_SR][1] === 1'b0)
             $display("--> [PASS] EXL bit correctly cleared on return.");
        else
             $display("--> [FAIL] Exception return failed, EXL not cleared.");
        @(posedge clk);

        $display("\n-----------------------------------");
        $display("--- CP0 Testbench Finished ---");
        $display("-----------------------------------");
        $finish;
    end

endmodule