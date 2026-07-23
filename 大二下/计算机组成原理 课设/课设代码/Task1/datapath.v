/*
 * 模块名称: datapath
 * 文件名称: datapath.v
 * 描述:     MIPS单周期处理器的数据通路。(支持MIPS-Lite1全部功能)
 */

`include "defines.v"

module datapath(
    // 全局信号
    input         clk,
    input         rst,
    
    // 来自控制器的控制信号
    input         RegWrite,
    input         ExtOp,
    input  [3:0]  ALUOp,
    input  [1:0]  PCSrc,
    input         RegDst,
    input         ALUSrc,
    input         MemWrite,
    input  [1:0]  WriteBackSel,
    input         JAL_Write,
    input         Ovf_WriteEnable,

    // 输出给控制器的状态/指令信号
    output [31:0] Instr,
    output        ALU_Zero,
    output        ALU_Overflow,
    output GPR_RD1_Sign // 输出 rs 寄存器值的符号位
);

    // --- 内部信号线 ---
    wire [31:0] npc_out, pc_out;
    wire [31:0] gpr_rd1, gpr_rd2;
    wire [31:0] ext_out;
    wire [31:0] alu_in_b;
    wire [31:0] alu_result;
    wire [31:0] dm_dout;
    wire [4:0]  gpr_write_addr;
    wire [31:0] gpr_write_data;
    wire [31:0] pc_plus_4;
    wire [31:0] lui_data;

    // --- 模块实例化 ---
    pc pc_unit (.clk(clk), .rst(rst), .NPC(npc_out), .PC(pc_out));
    npc npc_unit (.PC(pc_out), .SignImm(ext_out), .Instr_25_0(Instr[25:0]), .JR_Addr(gpr_rd1), .PCSrc(PCSrc), .NPC(npc_out));
    im im_unit (.addr(pc_out[9:0]), .dout(Instr));
    gpr gpr_unit (.clk(clk), .rst(rst), .RegWrite(RegWrite), .A1(Instr[25:21]), .A2(Instr[20:16]), .A3(gpr_write_addr), .WD3(gpr_write_data), .RD1(gpr_rd1), .RD2(gpr_rd2));
    ext ext_unit (.Imm16(Instr[15:0]), .ExtOp(ExtOp), .Imm32(ext_out));
    alu alu_unit (.A(gpr_rd1), .B(alu_in_b), .ALUOp(ALUOp), .Result(alu_result), .Zero(ALU_Zero), .Overflow(ALU_Overflow));
    dm dm_unit (.clk(clk), .rst(rst), .we(MemWrite), .addr(alu_result[9:0]), .din(gpr_rd2), .dout(dm_dout));

    // --- Muxes 和通路逻辑 ---
    assign pc_plus_4 = pc_out + 4;
    assign lui_data = {Instr[15:0], 16'b0};

    // GPR写地址选择逻辑
    wire [4:0] regdst_mux_out = RegDst ? Instr[15:11] : Instr[20:16];
    wire [4:0] jal_mux_out = JAL_Write ? 5'd31 : regdst_mux_out;
    assign gpr_write_addr = Ovf_WriteEnable ? 5'd30 : jal_mux_out;

    // ALU第二个操作数选择逻辑
    assign alu_in_b = ALUSrc ? ext_out : gpr_rd2;

    // GPR写数据选择逻辑 (4选1)
    reg [31:0] gpr_write_data_temp;
    always @(*) begin
        case (WriteBackSel)
            `WB_ALU:    gpr_write_data_temp = alu_result;
            `WB_MEM:    gpr_write_data_temp = dm_dout;
            `WB_PC4:    gpr_write_data_temp = pc_plus_4; // jal 使用 PC+4
            `WB_LUI:    gpr_write_data_temp = lui_data;
            default:    gpr_write_data_temp = 32'hxxxxxxxx;
        endcase
    end
    assign gpr_write_data = Ovf_WriteEnable ? 32'd1 : gpr_write_data_temp;
	 
	 assign GPR_RD1_Sign = gpr_rd1[31];

endmodule