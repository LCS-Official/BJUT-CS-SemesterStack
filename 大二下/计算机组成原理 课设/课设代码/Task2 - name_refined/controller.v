// 文件名: controller.v
`include "defines.v"

module controller (
    // ---------- 输入 ----------
    input           clk,
    input           rst,
    input   [5:0]   op,
    input   [5:0]   func,
    input           zero,

    // ---------- 输出控制信号 ----------
    // PC 控制
    output  reg [1:0]   PCSrc,
    output  reg         PCWrite,
    // IR 控制
    output  reg         IRWrite,
    // GPR 写回控制
    output  reg         RegWrite,
    output  reg [1:0]   RegDst,
    output  reg [1:0]   MemToReg,
    // 立即数扩展控制
    output  reg [1:0]   ExtOp,
    // ALU 控制
    output  reg [2:0]   ALUOp,
    output  reg         ALUSrc,
    // Memory 控制
    output  reg         MemWrite,
    output  reg         lb_en,
    output  reg         sb_en,
    // ALU 附加使能 (为清晰保留)
    output  reg         slt_en,
    output  reg         addi_en
);

    // FSM 状态定义
    localparam [3:0]
        S_FETCH     = 4'd0, // 状态0: 取指
        S_DECODE    = 4'd1, // 状态1: 译码/读寄存器
        S_MEM_ADDR  = 4'd2, // 状态2: 计算访存地址 (lw/sw)
        S_MEM_READ  = 4'd3, // 状态3: 读内存 (lw/lb)
        S_MEM_WB    = 4'd4, // 状态4: 内存数据写回GPR
        S_MEM_WRITE = 4'd5, // 状态5: 写内存 (sw/sb)
        S_EXEC      = 4'd6, // 状态6: R-type/I-type 指令执行
        S_ALU_WB    = 4'd7, // 状态7: ALU结果写回GPR
        S_BRANCH    = 4'd8, // 状态8: 分支跳转 (beq)
        S_JUMP      = 4'd9; // 状态9: J-type 指令跳转

    // ALU 操作定义
    localparam [2:0]
        ALU_ADD = 3'b000,
        ALU_SUB = 3'b001,
        ALU_OR  = 3'b010,
        ALU_SLT = 3'b011, // 自定义一个SLT操作码
        ALU_LUI = 3'b100; // 自定义一个LUI操作码

    // 状态机寄存器
    reg [3:0] current_state, next_state;

    // 指令类型解码
    wire is_Rtype = (op == `OP_RTYPE);
    wire is_addu  = (is_Rtype && func == `F_ADDU);
    wire is_subu  = (is_Rtype && func == `F_SUBU);
    wire is_slt   = (is_Rtype && func == `F_SLT);
    wire is_jr    = (is_Rtype && func == `F_JR);
    
    wire is_ori   = (op == `OP_ORI);
    wire is_lui   = (op == `OP_LUI);
    wire is_addi  = (op == `OP_ADDI);
    wire is_addiu = (op == `OP_ADDIU);

    wire is_lw    = (op == `OP_LW);
    wire is_sw    = (op == `OP_SW);
    wire is_lb    = (op == `OP_LB);
    wire is_sb    = (op == `OP_SB);
    wire is_mem   = is_lw | is_sw | is_lb | is_sb;

    wire is_beq   = (op == `OP_BEQ);
    wire is_j     = (op == `OP_J);
    wire is_jal   = (op == `OP_JAL);

    // --- FSM 第一部分: 时序逻辑 (状态转移) ---
    always @(posedge clk or posedge rst) begin
        if (rst)
            current_state <= S_FETCH;
        else
            current_state <= next_state;
    end

    // --- FSM 第二部分: 组合逻辑 (生成下一状态和控制信号) ---
    always @(*) begin
        // 1. 设置所有控制信号的默认值 (大多为无效状态)
        PCWrite  = 1'b0;
        IRWrite  = 1'b0;
        RegWrite = 1'b0;
        MemWrite = 1'b0;
        lb_en    = 1'b0;
        sb_en    = 1'b0;
        addi_en  = 1'b0;
        slt_en   = 1'b0;
        
        ALUSrc   = 1'b0; // 默认ALU第二操作数来自 寄存器(BusB)
        ExtOp    = 2'bxx;
        RegDst   = 2'bxx;
        MemToReg = 2'bxx;
        PCSrc    = 2'b00; // 默认PC更新为 PC+4
        ALUOp    = 3'bxxx;

        // 2. 根据当前状态和指令，确定下一状态和有效的控制信号
        case (current_state)
            S_FETCH: begin // 取指
                PCWrite = 1'b1;
                IRWrite = 1'b1;
                next_state = S_DECODE;
            end

            S_DECODE: begin // 译码
                ALUSrc = (is_Rtype | is_beq | is_jr) ? 1'b0 : 1'b1; // R/BEQ/JR用寄存器B, 其他用立即数
                
                if (is_mem)         next_state = S_MEM_ADDR;
                else if (is_Rtype)  next_state = S_EXEC;
                else if (is_beq)    next_state = S_BRANCH;
                else if (is_j || is_jal) next_state = S_JUMP;
                else                next_state = S_EXEC; // I-type (ori, addi, lui)
            end

            S_MEM_ADDR: begin // 计算访存地址
                ALUOp = ALU_ADD;
                if (is_lw || is_lb) next_state = S_MEM_READ;
                else                next_state = S_MEM_WRITE; // sw, sb
            end
            
            S_MEM_READ: begin // 读内存
                if(is_lw) lb_en = 1'b0; // 此处可根据DM设计简化
                if(is_lb) lb_en = 1'b1;
                next_state = S_MEM_WB;
            end

            S_MEM_WB: begin // 内存数据写回
                RegWrite = 1'b1;
                RegDst   = `REGDST_RT;
                MemToReg = `MEMTOREG_MEM;
                next_state = S_FETCH;
            end

            S_MEM_WRITE: begin // 写内存
                MemWrite = 1'b1;
                if(is_sw) sb_en = 1'b0;
                if(is_sb) sb_en = 1'b1;
                next_state = S_FETCH;
            end

            S_EXEC: begin // R-type或I-type ALU运算
                if (is_addu || is_addiu)  ALUOp = ALU_ADD;
                if (is_addi)            begin ALUOp = ALU_ADD; addi_en = 1'b1;end
                if (is_subu)              ALUOp = ALU_SUB;
                if (is_ori)               ALUOp = ALU_OR;
                if (is_slt)             begin ALUOp = ALU_SLT; slt_en = 1'b1;end
                if (is_lui)               ALUOp = ALU_LUI; // LUI可特殊处理
                
                next_state = S_ALU_WB;
            end

            S_ALU_WB: begin // ALU结果写回
                RegWrite = 1'b1;
                RegDst   = (is_Rtype) ? `REGDST_RD : `REGDST_RT;
                MemToReg = `MEMTOREG_ALU;
                next_state = S_FETCH;
            end
            
            S_BRANCH: begin // 分支
                ALUOp = ALU_SUB; // 用于比较
                if (zero) begin
                    PCWrite = 1'b1;
                    PCSrc = `PCSRC_BRANCH;
                end
                next_state = S_FETCH;
            end

            S_JUMP: begin // 跳转
                PCWrite  = 1'b1;
                PCSrc    = is_j ? `PCSRC_JUMP : (is_jr ? `PCSRC_JR : `PCSRC_JUMP) ; // JAL也用JUMP地址
                RegWrite = is_jal; // JAL需要写返回地址
                RegDst   = `REGDST_RA;
                MemToReg = `MEMTOREG_PC4;
                next_state = S_FETCH;
            end

            default: begin
                next_state = S_FETCH;
            end
        endcase

        // 3. ExtOp信号单独处理，因为它依赖于指令而不是状态
        if (is_ori)             ExtOp = `EXTOP_ZERO;
        else if (is_lui)        ExtOp = `EXTOP_LUI;
        else                    ExtOp = `EXTOP_SIGN; // 默认符号扩展
    end

endmodule