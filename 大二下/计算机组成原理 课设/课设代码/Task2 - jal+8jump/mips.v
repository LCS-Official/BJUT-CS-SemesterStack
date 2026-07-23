/*
 * --------------------------------------------------------------------
 * 模块名称: mips
 * 文件名称: mips.v
 * 描述:     MIPS多周期处理器顶层模块。
 * --------------------------------------------------------------------
 */
module mips(
    input clk,
    input rst
);

    // --- 内部信号线 ---
    // controller -> datapath
    wire        w_reg_write, w_mem_write, w_pc_write, w_pc_write_cond, w_ir_write, w_ext_op;
    wire [1:0]  w_pc_src, w_alu_src_a, w_alu_src_b, w_wb_sel;
    wire [3:0]  w_alu_op;
    wire [1:0]  w_gpr_write_addr_sel;

    // datapath -> controller
    wire [5:0] w_opcode, w_funct;
    wire       w_alu_zero;


    // --- 模块实例化 ---
    datapath datapath_unit (
        .clk(clk), .rst(rst),
        .RegWrite(w_reg_write), .MemWrite(w_mem_write),
        .PCWrite(w_pc_write), .IRWrite(w_ir_write),
        .ExtOp(w_ext_op), .PCSrc(w_pc_src),
        .ALUSrcA(w_alu_src_a), .ALUSrcB(w_alu_src_b),
        .WriteBackSel(w_wb_sel), .GPRWriteAddrSel(w_gpr_write_addr_sel),
        .ALUOp(w_alu_op),
        .Opcode(w_opcode), .Funct(w_funct), .ALU_Zero(w_alu_zero)
    );

    controller controller_unit (
        .clk(clk), .rst(rst),
        .Opcode(w_opcode), .Funct(w_funct), .ALU_Zero(w_alu_zero),
        .RegWrite(w_reg_write), .MemWrite(w_mem_write),
        .PCWrite(w_pc_write), .IRWrite(w_ir_write),
        .ExtOp(w_ext_op), .PCSrc(w_pc_src),
        .ALUSrcA(w_alu_src_a), .ALUSrcB(w_alu_src_b),
        .WriteBackSel(w_wb_sel), .GPRWriteAddrSel(w_gpr_write_addr_sel),
        .ALUOp(w_alu_op)
    );

endmodule