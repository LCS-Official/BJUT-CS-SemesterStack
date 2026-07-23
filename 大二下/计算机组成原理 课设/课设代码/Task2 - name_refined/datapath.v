/*
 * --------------------------------------------------------------------
 * 模块名称: datapath
 * 文件名称: datapath.v
 * 描述:     MIPS多周期处理器的数据通路。
 * --------------------------------------------------------------------
 */

module datapath(
    // 控制信号输入 (来自 Controller)
    input           clk,
    input           rst,
    input   [1:0]   reg_sel,
    input   [1:0]   WriteBackSel,
    input   [1:0]   PCSrc,
    input   [1:0]   ExtOp,
    input           we,
    input           RegWrite,
    input           alu_sel,
    input           addien,
    input           slt_en,
    input           lb_en,
    input           sb_en,
    input           pcwr,
    input           IRWrite,
	 input   [2:0]   ALUOp,

    // 状态/指令信号输出 (送往 Controller)
    output  [5:0]   Opcode,
    output  [5:0]   Funct,
    output          ALU_Zero
);

    // 内部连线
    wire [31:0] insout, nxtpc, curpc, pc_add4, wd, sbout, lbout;
    wire [31:0] busA, busB, B, extout, alu_out, dmout, busAout, busBout, alu_outout;
    wire [25:0] imm26;
    wire [15:0] imm16;
    wire [4:0]  rs, rt, rd, rw;
    wire        overflow;
	 wire [5:0] op_wire, func_wire;
    wire zero_wire;

    // 将控制器输出的 ALUOp 连接到 ALU (注意：这里的名称映射需要对齐)
    // 在 controller.v 中，ALUOp 是 3-bit 的，但旧的 alu 实例似乎用了 2-bit。
    // 这里假设 alu1 实例的 alu_op 端口应该是 3-bit，以匹配新的控制器。
    // 如果 alu1 确实是 2-bit，则需要一个转换逻辑或修改 alu1。
    // 为保持与您原始 mips.v 的连接一致，我将使用 wire [2:0] alu_op;
    // 并将它连接到控制器的 ALUOp 端口。
    // 请确保您的 alu 模块的 alu_op 输入是3位的。
    // wire [2:0] alu_op; // This would come from controller's ALUOp
    
    //----------------------------------------------------
    // 数据通路逻辑 (Muxes)
    //----------------------------------------------------
    assign rw = (reg_sel == 2'b00) ? rt : 
                (reg_sel == 2'b01) ? rd : 5'b11111; // 对应 REG_DEST_RT/RD

    // WriteBackSel: 00=ALU, 01=MEM, 10=PC+4
    assign wd = (WriteBackSel == 2'b00) ? alu_outout : 
                (WriteBackSel == 2'b01) ? lbout : pc_add4;
    
    assign B = alu_sel ? extout : busBout;
    assign sbout = busBout;
    assign lbout = dmout;

    // 将 IR 的输出连接到数据通路的顶层输出
    assign Opcode = op_wire;
    assign Funct = func_wire;
    assign ALU_Zero = zero_wire;

    //----------------------------------------------------
    // 模块实例化
    //----------------------------------------------------
    pc          PC( .clk(clk), .rst(rst), .NPC(nxtpc), .PC(curpc), .PCWrite(pcwr) );
    im          IM( .addr(curpc[9:0]), .dout(insout) );
    ir          IR( .clk(clk), .ins(insout), .rs(rs), .rt(rt), .rd(rd), .func(func_wire), .OpCode(op_wire), .imm26(imm26), .IRWrite(IRWrite) );
    gpr         GPR( .clk(clk), .rst(rst), .rs(rs), .rt(rt), .rw(rw), .wd(wd), .RegWrite(RegWrite), .busA(busA), .busB(busB), .addi_overflow(overflow) );
    ext         EXT( .imm16(imm26[15:0]), .imm32(extout), .ExtOp(ExtOp) );
    npc         NPC( .PC(curpc), .Instr_25_0(imm26), .register(busA), .PCSrc(PCSrc), .zero(zero_wire), .NPC(nxtpc), .pc_add4(pc_add4) );
    
    // 中间寄存器
    rega        RegA( .clk(clk), .din(busA), .dout(busAout) );
    regb        RegB( .clk(clk), .din(busB), .dout(busBout) );
    
    // ALU 单元
    // 注意: 请确认您的 alu 模块定义与此处的端口连接一致
    // 特别是 slten 和 addien，在优化后的 controller.v 中已整合，此处直接连接
    alu         ALU( .A(busAout), .B(B), .ALUOp(ALUOp), .zero(zero_wire), .alu_out(alu_out), .slt(slt_en), .addi(addien) );

    regaluout   RegALUOut( .clk(clk), .din(alu_out), .dout(alu_outout) );
    
    // 数据存储器
    dm          DM( .addr(alu_outout[9:0]), .din(sbout), .we(we), .clk(clk), .dout(dmout), .lb_en(lb_en), .sb_en(sb_en) );
    
endmodule