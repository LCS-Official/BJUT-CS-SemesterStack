`timescale 1ns / 1ps
`include "defines.v"

module test_datapath_tb;

    // 1. Inputs to Datapath (Control Signals)
    reg         clk, rst;
    reg         RegWrite;
    reg         ExtOp;
    reg  [3:0]  ALUOp;
    reg  [1:0]  PCSrc;
    reg         RegDst;
    reg         ALUSrc;
    reg         MemWrite;
    reg         MemtoReg;

    // 2. Outputs from Datapath
    wire [31:0] Instr;
    wire        ALU_Zero;

    // 3. Instantiate the Datapath
    datapath uut (
        .clk(clk), .rst(rst),
        .RegWrite(RegWrite), .ExtOp(ExtOp), .ALUOp(ALUOp), .PCSrc(PCSrc),
        .RegDst(RegDst), .ALUSrc(ALUSrc), .MemWrite(MemWrite), .MemtoReg(MemtoReg),
        .Instr(Instr), .ALU_Zero(ALU_Zero)
    );

    // 4. Clock Generator
    initial clk = 0;
    always #5 clk = ~clk;

    // 5. Test Sequence
    initial begin
        // --- Global Setup ---
        rst = 1;
        #15; // Assert reset
        rst = 0;
        $display("\n------ Datapath Simulation Start ------");

        // --- Test 1: addu $t2, $t0, $t1 ---
        $display("\n[Test 1] Simulating `addu $t2, $t0, $t1`...");
        
        // --- Setup State (扮演加载器的角色) ---
        // 使用层次化引用，强制设置寄存器的初始值
        // uut.gpr_unit 是datapath模块里gpr模块的实例名
        uut.gpr_unit.registers[8] = 32'd10; // $t0 = 10
        uut.gpr_unit.registers[9] = 32'd20; // $t1 = 20
        $display("    Setup: $t0=10, $t1=20");
        
        // --- Execute Cycle 1: Fetch `addu` ---
        @(posedge clk); // PC复位后指向0x3000, 此刻取出addu指令
        #1; // 等待指令在Instr总线上稳定
        $display("    Cycle 1: Fetched instruction at 0x3000: %h", Instr);
        
        // --- Execute Cycle 2: Execute `addu` (扮演控制器的角色) ---
        $display("    Cycle 2: Setting control signals for `addu`...");
        RegWrite = 1;      // 要写入GPR
        RegDst   = 1;      // 写目标是rd字段($t2)
        ALUSrc   = 0;      // ALU第二个操作数来自GPR
        MemtoReg = 0;      // 写回GPR的数据来自ALU
        MemWrite = 0;      // 不写DM
        ExtOp    = 1'bx;   // 扩展单元不用，设为x(不定)
        ALUOp    = `ALU_ADD; // ALU执行加法
        PCSrc    = `PC_SRC_P4; // PC正常+4
        
        @(posedge clk); // addu指令执行完毕，结果写入$t2
        
        // --- Verification ---
        #1;
        $display("    Verification: Value of $t2(10) is %d", uut.gpr_unit.registers[10]);
        if (uut.gpr_unit.registers[10] == 30)
            $display("    SUCCESS: addu test passed!");
        else
            $display("    FAILURE: addu test failed!");
            
        // --- Test 2: lw $t3, 4($t0) ---
        $display("\n[Test 2] Simulating `lw $t3, 4($t0)`...");
        
        // --- Setup State ---
        // $t0的值仍然是10。我们需要在DM中预存一个值。
        // 目标地址 = $t0 + 4 = 10 + 4 = 14。
        // 我们在DM地址14处存入0xFEEDFACE (小端序)
        uut.dm_unit.dm[14] = 8'hCE; 
        uut.dm_unit.dm[15] = 8'hFA;
        uut.dm_unit.dm[16] = 8'hED;
        uut.dm_unit.dm[17] = 8'hFE;
        $display("    Setup: Stored 0xFEEDFACE at memory address 14");
        
        // --- Execute Cycle 3: Fetch `lw` ---
        // PC在上一周期已更新为0x3004, 此刻取出lw指令
        #1; 
        $display("    Cycle 3: Fetched instruction at 0x3004: %h", Instr);
        
        // --- Execute Cycle 4: Execute `lw` ---
        $display("    Cycle 4: Setting control signals for `lw`...");
        RegWrite = 1;      // 要写入GPR
        RegDst   = 0;      // 写目标是rt字段($t3)
        ALUSrc   = 1;      // ALU第二个操作数来自立即数
        MemtoReg = 1;      // 写回GPR的数据来自DM
        MemWrite = 0;      // 不写DM
        ExtOp    = 1'b1;   // 立即数需要符号扩展
        ALUOp    = `ALU_ADD; // ALU执行加法计算地址
        PCSrc    = `PC_SRC_P4; // PC正常+4
        
        @(posedge clk); // lw指令执行完毕，数据写入$t3
        
        // --- Verification ---
        #1;
        $display("    Verification: Value of $t3(11) is %h", uut.gpr_unit.registers[11]);
        if (uut.gpr_unit.registers[11] == 32'hFEEDFACE)
            $display("    SUCCESS: lw test passed!");
        else
            $display("    FAILURE: lw test failed!");

        $display("\n------ Datapath Simulation End ------");
        $finish;
    end
endmodule