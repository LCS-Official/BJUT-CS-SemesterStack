// =================================================================================
// Testbench for: bridge
// Description:   This testbench specifically verifies the functionality of the
//                bridge module, including address decoding, read/write routing,
//                and interrupt mapping.
// =================================================================================
`timescale 1ns/1ps

module bridge_tb;

    // --------------------------------------------------------------------------
    // 1. Signal Declarations
    // --------------------------------------------------------------------------
    
    // -- Inputs to the bridge (driven by this testbench) --
    reg [31:0] praddr;      // Simulates the address from the CPU
    reg [31:0] bridgedin;   // Simulates the write-data from the CPU
    reg [31:0] dev0_rd;     // Simulates the read-data from Device 0 (Timer)
    reg [31:0] dev1_rd;     // Simulates the read-data from Device 1 (Switch)
    reg [31:0] dev2_rd;     // Simulates the read-data from Device 2 (Output Dev)
    reg        devwr;       // Simulates the master write-enable from the CPU
    reg        irq;         // Simulates the interrupt request from the Timer
    reg        chan;

    // -- Outputs from the bridge (to be monitored) --
    wire [31:0] cpu_rd;      // Data read by the CPU
    wire [31:0] dev_wd;      // Data to be written to devices
    wire [3:0]  dev_addr;    // Decoded intra-device address
    wire        dev0_we;     // Write-enable for Device 0
    wire        dev2_we;     // Write-enable for Device 2
    wire [5:0]  hwint;       // Hardware interrupt vector to CP0
    wire        change;

    // --------------------------------------------------------------------------
    // 2. Instantiate the Device Under Test (DUT)
    // --------------------------------------------------------------------------
    
    // Using named port connections for clarity and robustness
    bridge dut (
        .praddr     (praddr),
        .bridgedin  (bridgedin),
        .cpu_rd     (cpu_rd),
        .dev0_rd    (dev0_rd),
        .dev1_rd    (dev1_rd),
        .dev2_rd    (dev2_rd),
        .dev_wd     (dev_wd),
        .dev_addr   (dev_addr),
        .devwr      (devwr),
        .dev0_we    (dev0_we),
        .dev2_we    (dev2_we),
        .hwint      (hwint),
        .irq        (irq),
        .change     (change),
        .chan       (chan)
    );

    // --------------------------------------------------------------------------
    // 3. Test Sequence
    // --------------------------------------------------------------------------
    
    initial begin
        $display("--------------------------------------------------");
        $display("--- Starting Bridge Module Testbench ---");
        $display("--------------------------------------------------");

        // -- Initialization --
        praddr    = 32'h0;
        bridgedin = 32'h0;
        dev0_rd   = 32'hAAAAAAAA; // Pre-load simulated device data
        dev1_rd   = 32'hBBBBBBBB;
        dev2_rd   = 32'hCCCCCCCC;
        devwr     = 1'b0;
        irq       = 1'b0;
        chan      = 1'b0;
        #10;

        // --- Test Case 1: Write to Timer (Device 0) ---
        $display("\n[TC1] Testing Write to Timer (Device 0)...");
        praddr    = 32'h0000_7f04; // Address for timer's initial value reg
        bridgedin = 32'h0001_86A0; // A sample value to write
        devwr     = 1'b1;
        #10;
        if (dev0_we === 1'b1 && dev2_we === 1'b0 && dev_wd === 32'h0001_86A0)
            $display("--> [PASS] Correctly enabled dev0 for writing.");
        else
            $display("--> [FAIL] Incorrect write enable logic for dev0.");
        devwr = 1'b0; // End write cycle
        #10;

        // --- Test Case 2: Write to Output Device (Device 2) ---
        $display("\n[TC2] Testing Write to Output Device (Device 2)...");
        praddr    = 32'h0000_7f20; // Address for output device
        bridgedin = 32'hDEADBEEF;
        devwr     = 1'b1;
        #10;
        if (dev2_we === 1'b1 && dev0_we === 1'b0 && dev_wd === 32'hDEADBEEF)
            $display("--> [PASS] Correctly enabled dev2 for writing.");
        else
            $display("--> [FAIL] Incorrect write enable logic for dev2.");
        devwr = 1'b0; // End write cycle
        #10;

        // --- Test Case 3: Write to an invalid (non-device) address ---
        $display("\n[TC3] Testing Write to invalid address...");
        praddr    = 32'h0000_1000; // An address in data memory space
        bridgedin = 32'hFFFFFFFF;
        devwr     = 1'b1;
        #10;
        if (dev0_we === 1'b0 && dev2_we === 1'b0)
            $display("--> [PASS] Correctly kept all devices disabled.");
        else
            $display("--> [FAIL] A device was incorrectly enabled.");
        devwr = 1'b0;
        #10;

        // --- Test Case 4: Read from Timer (Device 0) ---
        $display("\n[TC4] Testing Read from Timer (Device 0)...");
        praddr = 32'h0000_7f08; // Address for timer's counter reg
        #10;
        if (cpu_rd === 32'hAAAAAAAA)
            $display("--> [PASS] Correctly read data from dev0.");
        else
            $display("--> [FAIL] Incorrect data or high-Z on read from dev0. Got %h", cpu_rd);
        #10;

        // --- Test Case 5: Read from Switch (Device 1) ---
        $display("\n[TC5] Testing Read from Switch (Device 1)...");
        praddr = 32'h0000_7f10;
        #10;
        if (cpu_rd === 32'hBBBBBBBB)
            $display("--> [PASS] Correctly read data from dev1.");
        else
            $display("--> [FAIL] Incorrect data or high-Z on read from dev1. Got %h", cpu_rd);
        #10;
        
        // --- Test Case 6: Read from an invalid (non-device) address ---
        $display("\n[TC6] Testing Read from invalid address...");
        praddr = 32'h0000_2000; // Another data memory address
        #10;
        if (cpu_rd === 32'bzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz)
            $display("--> [PASS] Correctly output high-impedance (Z).");
        else
            $display("--> [FAIL] Expected high-Z but got %h", cpu_rd);
        #10;

        // --- Test Case 7: Test dev_addr and hwint ---
        $display("\n[TC7] Testing dev_addr and hwint generation...");
        praddr = 32'h0000_7f24; // Use dev2's second address
        irq = 1'b1;
        #10;
        if (dev_addr === 4'b1001 && hwint === 6'b000001)
            $display("--> [PASS] Correctly generated dev_addr and hwint.");
        else
            $display("--> [FAIL] Incorrect dev_addr or hwint. Got dev_addr=%b, hwint=%b", dev_addr, hwint);
        irq = 1'b0;
        #10;


        $display("\n--------------------------------------------------");
        $display("--- Testbench Finished ---");
        $display("--------------------------------------------------");
        $finish;
    end

endmodule