// rtl/datapath.v
`include "defines.v"
module datapath(
    input clk,
    input rst,

    // Control signals from Controller
    input pc_write,
    input ir_write,
    input reg_write,
    input mem_read,
    input mem_write,
    input sign_ext_en,
    input [1:0] reg_dst,
    input gpr_dst_load, //new
    input [1:0] alu_src_a,
    input [1:0] alu_src_b,
    input [1:0] mem_to_reg,
    input [1:0] next_pc_sel,  // <--- Controller发来的NPC选择信号
    input [3:0] alu_op,
    input [1:0] dm_data_size,

    // Outputs to Controller
    output [5:0] op,
    output [5:0] funct,
    output zero,
    output overflow
);

    // Wires for inter-module connections
    wire [31:0] pc_current;
    wire [31:0] pc_next; // 这是最终要送给PC寄存器的下一地址
    wire [31:0] instruction;
    wire [31:0] gpr_read_data1, gpr_read_data2;
    wire [31:0] extended_imm;
    wire [31:0] alu_in_a, alu_in_b;
    wire [31:0] alu_result;
    wire [31:0] dm_read_data;
    wire [4:0]  gpr_write_reg;
    wire [31:0] gpr_write_data;
	 
	 wire [31:0] pc_plus_4;
    wire [31:0] branch_addr;
    wire [31:0] jump_addr;
    wire [31:0] jr_addr;

    // Intermediate Registers
    reg [31:0] ir;
    reg [31:0] mdr;
    reg [31:0] a_reg, b_reg;
    reg [31:0] alu_out_reg;
	 reg [4:0] gpr_write_reg_saved;

    // Decoding instruction fields from IR
    assign op    = ir[31:26];
    assign funct = ir[5:0];

    // Instantiate Core Modules (PC, IM, GPR, ALU, EXT, DM)
    pc pc_reg(clk, rst, pc_write, pc_next, pc_current); // pc_next 由下面的NPC逻辑产生
    im instr_mem(pc_current, instruction);
	 gpr reg_file(
		  .clk        (clk),
		  .rst        (rst),
		  .reg_write  (reg_write),
		  .read_reg1  (ir[25:21]),
		  .read_reg2  (ir[20:16]),
		  .write_data (gpr_write_data),
		  .write_reg(gpr_write_reg_saved),
		  .read_data1 (gpr_read_data1),
	 	  .read_data2 (gpr_read_data2)
	 );
    ext extender(ir[15:0], sign_ext_en, extended_imm);
    alu alu_unit(alu_in_a, alu_in_b, alu_op, alu_result, zero, overflow);
    dm data_mem(clk, mem_read, mem_write, alu_out_reg, b_reg, dm_data_size, dm_read_data);

    // ======================================================================
    // === NPC 功能核心逻辑 (内嵌于Datapath) ================================
    // ======================================================================
    // 使 pc_next 成为 reg 类型，以便在 always 块中赋值
    reg [31:0] pc_next_reg; 
    assign pc_next = pc_next_reg;

	 
    // --- Assign NPC source wires ---
    assign pc_plus_4   = pc_current + 4;
    assign branch_addr = pc_plus_4 + (extended_imm << 2);
    assign jump_addr   = {pc_plus_4[31:28], ir[25:0], 2'b00};
    assign jr_addr     = a_reg; // jr 的地址来自寄存器 a_reg
	 
	 
    always @(*) begin
        // 根据来自Controller的 next_pc_sel 信号，选择正确的下一PC地址
        case(next_pc_sel)
            2'b01: begin // 分支指令 (BEQ)
                if (zero)
                    pc_next_reg = branch_addr; // 条件满足，选择分支地址
                else
                    pc_next_reg = pc_plus_4;   // 条件不满足，顺序执行
            end
            2'b10: begin // 跳转指令 (J, JAL)
                pc_next_reg = jump_addr;
            end
            2'b11: begin // 寄存器跳转 (JR)
                pc_next_reg = jr_addr;
            end
            default: begin // 默认或顺序执行 (next_pc_sel == 2'b00)
                pc_next_reg = pc_plus_4;
            end
        endcase
    end
    // ======================================================================
    
    // Intermediate Registers Logic
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            ir <= 32'b0;
            a_reg <= 32'b0;
            b_reg <= 32'b0;
            alu_out_reg <= 32'b0;
				gpr_write_reg_saved <= 5'b0;
        end else begin
				if (gpr_dst_load) begin // 当控制器信号有效时，锁存目标地址
                gpr_write_reg_saved <= gpr_write_reg; // gpr_write_reg 是之前 Mux 的输出
            end
            if (ir_write) ir <= instruction;
            a_reg <= gpr_read_data1;
            b_reg <= gpr_read_data2;
            alu_out_reg <= alu_result;
        end
    end
    always @(posedge clk) begin
         mdr <= dm_read_data;
    end
    
    // Mux for ALU input A
    assign alu_in_a = (alu_src_a == 2'b00) ? pc_current : // for PC+4
                      (alu_src_a == 2'b01) ? a_reg :
                      a_reg;

    // Mux for ALU input B
    assign alu_in_b = (alu_src_b == 2'b00) ? b_reg :
                      (alu_src_b == 2'b01) ? 32'd4 : // for PC+4
                      (alu_src_b == 2'b10) ? extended_imm :
                      extended_imm;

    // Mux for GPR Write Register
    assign gpr_write_reg = (reg_dst == 2'b00) ? ir[20:16] : // rt
                           (reg_dst == 2'b01) ? ir[15:11] : // rd
                           (reg_dst == 2'b10) ? 5'd31 : // $ra for jal
                           5'd30; // for addi overflow, not currently used with reg_dst

    // Mux for GPR Write Data
    assign gpr_write_data = (mem_to_reg == 2'b00) ? alu_out_reg :
                            (mem_to_reg == 2'b01) ? mdr :
                            (mem_to_reg == 2'b10) ? (pc_current + 4) : // For jal write back PC+4
                            alu_out_reg;
endmodule