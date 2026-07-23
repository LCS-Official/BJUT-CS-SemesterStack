/*
 * --------------------------------------------------------------------
 * 模块名称: datapath
 * 文件名称: datapath.v
 * 描述:     MIPS多周期处理器的数据通路。
 * --------------------------------------------------------------------
 */
`include "defines.v"

module datapath(
    input clk, rst,
    input        RegWrite, MemWrite, PCWrite, IRWrite, ExtOp,
    input [1:0]  PCSrc, ALUSrcA, ALUSrcB, WriteBackSel, GPRWriteAddrSel,
    input [3:0]  ALUOp,
    output [5:0] Opcode, Funct,
    output       ALU_Zero
);
    // --- 中间寄存器 ---
    reg [31:0] instr_reg;
    reg [31:0] gpr_data_a, gpr_data_b;
    reg [31:0] alu_out_reg;
    reg [31:0] mem_data_reg;

    // --- 模块输出/内部信号线 ---
    wire [31:0] pc_out, npc_out;
    wire [31:0] instr_mem_out;
    wire [31:0] gpr_rd1_out, gpr_rd2_out;
    wire [31:0] ext_out;
    wire [31:0] alu_in_a, alu_in_b, alu_result;
    wire [31:0] mem_read_out;
    wire [4:0]  gpr_write_addr;
    wire [31:0] gpr_write_data;

    // --- 提取 Opcode 和 Funct ---
    assign Opcode = instr_reg[31:26];
    assign Funct = instr_reg[5:0];
    
    // --- 1. PC 和指令获取 ---
    pc pc_unit(.clk(clk), .rst(rst), .PCWrite(PCWrite), .NPC(npc_out), .PC(pc_out));
    
    im im_unit (.addr(pc_out[9:0]), .dout(instr_mem_out));

    // NPC 模块，用于计算所有可能的下一PC
    npc npc_unit(
        .PC(pc_out), 
        .SignImm(ext_out), 
        .Instr_25_0(instr_reg[25:0]), 
        .JR_Addr(gpr_data_a), 
        .PCSrc(PCSrc), 
        .NPC(npc_out)
    );
    
    // 指令寄存器 (IR)
    always @(posedge clk or posedge rst) begin
        if (rst) instr_reg <= 32'b0;
        else if (IRWrite) instr_reg <= instr_mem_out;
    end

    // --- 2. 译码/读寄存器 ---
    gpr gpr_unit (
        .clk(clk), .rst(rst), .RegWrite(RegWrite),
        .A1(instr_reg[25:21]), .A2(instr_reg[20:16]),
        .A3(gpr_write_addr), .WD3(gpr_write_data),
        .RD1(gpr_rd1_out), .RD2(gpr_rd2_out)
    );

    ext ext_unit (.Imm16(instr_reg[15:0]), .ExtOp(ExtOp), .Imm32(ext_out));

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            gpr_data_a <= 32'b0;
            gpr_data_b <= 32'b0;
        end else begin
            gpr_data_a <= gpr_rd1_out;
            gpr_data_b <= gpr_rd2_out;
        end
    end
    
    // --- 3. 执行 ---
    assign alu_in_a = (ALUSrcA == 2'b00) ? pc_out :
                      (ALUSrcA == 2'b01) ? gpr_data_a :
                      32'hxxxxxxxx;
                      
    assign alu_in_b = (ALUSrcB == 2'b00) ? gpr_data_b :
                      (ALUSrcB == 2'b01) ? 32'd4 :
                      (ALUSrcB == 2'b10) ? ext_out :
                      (ALUSrcB == 2'b11) ? (ext_out << 2) :
                      32'hxxxxxxxx;

    alu alu_unit (.A(alu_in_a), .B(alu_in_b), .ALUOp(ALUOp), .Result(alu_result), .Zero(ALU_Zero), .Overflow());

    always @(posedge clk or posedge rst) begin
        if (rst) alu_out_reg <= 32'b0;
        else alu_out_reg <= alu_result;
    end

    // --- 4. 访存 ---
    dm dm_unit (.clk(clk), .rst(rst), .we(MemWrite), .addr(alu_out_reg[9:0]), .din(gpr_data_b), .dout(mem_read_out));
    
    always @(posedge clk or posedge rst) begin
        if (rst) mem_data_reg <= 32'b0;
        else mem_data_reg <= mem_read_out;
    end

    // --- 5. 写回 ---
    assign gpr_write_addr = (GPRWriteAddrSel == 2'b00) ? instr_reg[20:16] : // rt
                            (GPRWriteAddrSel == 2'b01) ? instr_reg[15:11] : // rd
                            (GPRWriteAddrSel == 2'b10) ? 5'd31 : // $ra for jal
                            5'hxx; 

    assign gpr_write_data = (WriteBackSel == 2'b00) ? alu_out_reg :
                            (WriteBackSel == 2'b01) ? mem_data_reg :
                            32'hxxxxxxxx; // Removed the direct PC+4 path
endmodule
