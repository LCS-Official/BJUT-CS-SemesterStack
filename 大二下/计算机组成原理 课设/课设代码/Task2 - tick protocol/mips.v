// mips.v
`include "defines.v"
module mips(
    input clk,
    input rst
);

    wire [5:0] op, funct;
    wire zero, overflow;

    wire pc_write, ir_write, reg_write, mem_read, mem_write;
    wire sign_ext_en;
    wire [1:0] reg_dst;
    wire [1:0] alu_src_a, alu_src_b;
    wire [1:0] mem_to_reg;
    wire [1:0] next_pc_sel;
    wire [3:0] alu_op;
    wire [1:0] dm_data_size;
	 wire gpr_dst_load;

    datapath u_datapath (
        .clk(clk), .rst(rst),
        .pc_write(pc_write), .ir_write(ir_write), .reg_write(reg_write),
        .mem_read(mem_read), .mem_write(mem_write), .sign_ext_en(sign_ext_en),
        .reg_dst(reg_dst), .alu_src_a(alu_src_a), .alu_src_b(alu_src_b),
        .mem_to_reg(mem_to_reg), .next_pc_sel(next_pc_sel), .alu_op(alu_op),
        .dm_data_size(dm_data_size),
        .op(op), .funct(funct), .zero(zero), .overflow(overflow),
		  .gpr_dst_load(gpr_dst_load)
    );

    controller u_controller (
        .clk(clk), .rst(rst),
        .op(op), .funct(funct), .zero(zero), .overflow(overflow),
        .pc_write(pc_write), .ir_write(ir_write), .reg_write(reg_write),
        .mem_read(mem_read), .mem_write(mem_write), .sign_ext_en(sign_ext_en),
        .reg_dst(reg_dst), .alu_src_a(alu_src_a), .alu_src_b(alu_src_b),
        .mem_to_reg(mem_to_reg), .next_pc_sel(next_pc_sel), .alu_op(alu_op),
        .dm_data_size(dm_data_size)
    );

endmodule