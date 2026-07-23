/*
 * --------------------------------------------------------------------
 * 模块名称: controller
 * 文件名称: controller.v
 * 描述:     MIPS多周期处理器的FSM控制器。
 * --------------------------------------------------------------------
 */

// 包含宏定义文件
`include "defines.v"

module controller(
    input           clk,
    input           ALU_Zero,
    input   [5:0]   Opcode,
    input   [5:0]   Funct,
    
    // 模块选择信号
    output  [1:0]   reg_sel,
    output  [1:0]   WriteBackSel,
    output  [1:0]   PCSrc,
    output  [1:0]   ExtOp,
    output  [2:0]   ALUOp,

    // 模块使能信号
    output          we,
    output          RegWrite,
    output          addien,
    output          slt_en,
    output          alu_sel,
    output          sb_en,
    output          lb_en,
    output          pcwr,
    output          IRWrite
);
    
    // 状态机寄存器
    reg [3:0] fsm;

    // FSM 状态线
    wire fs0, fs1, fs2, fs3, fs4, fs5, fs6, fs7, fs8, fs9;

    // 初始化 FSM
    initial begin
        fsm = `STATE_FETCH;
    end
    
    //----------------------------------------------------
    // 指令译码
    //----------------------------------------------------
    wire addu   = (Opcode == `OPCODE_R_TYPE) && (Funct == `FUNCT_ADDU);
    wire subu   = (Opcode == `OPCODE_R_TYPE) && (Funct == `FUNCT_SUBU);
    wire slt    = (Opcode == `OPCODE_R_TYPE) && (Funct == `FUNCT_SLT);
    wire jr     = (Opcode == `OPCODE_R_TYPE) && (Funct == `FUNCT_JR);
    wire ori    = (Opcode == `OPCODE_ORI);
    wire lw     = (Opcode == `OPCODE_LW);
    wire sw     = (Opcode == `OPCODE_SW);
    wire beq    = (Opcode == `OPCODE_BEQ);
    wire lui    = (Opcode == `OPCODE_LUI);
    wire j      = (Opcode == `OPCODE_J);
    wire addiu  = (Opcode == `OPCODE_ADDIU);
    wire addi   = (Opcode == `OPCODE_ADDI);
    wire jal    = (Opcode == `OPCODE_JAL);
    wire lb     = (Opcode == `OPCODE_LB);
    wire sb     = (Opcode == `OPCODE_SB);

    //----------------------------------------------------
    // 状态机状态分配
    //----------------------------------------------------
    assign fs0 = (fsm == `STATE_FETCH);
    assign fs1 = (fsm == `STATE_DECODE);
    assign fs2 = (fsm == `STATE_MEM_ADDR);
    assign fs3 = (fsm == `STATE_MEM_READ);
    assign fs4 = (fsm == `STATE_MEM_WB);
    assign fs5 = (fsm == `STATE_MEM_WRITE);
    assign fs6 = (fsm == `STATE_EXECUTE);
    assign fs7 = (fsm == `STATE_ALU_WB);
    assign fs8 = (fsm == `STATE_BRANCH);
    assign fs9 = (fsm == `STATE_JUMP);
    
    //----------------------------------------------------
    // 状态机时序逻辑 (状态转移)
    //----------------------------------------------------
    always @(posedge clk) begin
        case(fsm)
            `STATE_FETCH:   fsm <= `STATE_DECODE;
            `STATE_DECODE:
                if (sw | lw | sb | lb)                      fsm <= `STATE_MEM_ADDR;
                else if (addu | subu | ori | lui | addi | addiu | slt | jr) fsm <= `STATE_EXECUTE;
                else if (beq)                               fsm <= `STATE_BRANCH;
                else if (j | jal)                           fsm <= `STATE_JUMP;
                else                                        fsm <= `STATE_FETCH; // Default case for unsupported instructions
            `STATE_MEM_ADDR:
                if (lw | lb)                                fsm <= `STATE_MEM_READ;
                else                                        fsm <= `STATE_MEM_WRITE;
            `STATE_MEM_READ:    fsm <= `STATE_MEM_WB;
            `STATE_MEM_WB:      fsm <= `STATE_FETCH;
            `STATE_MEM_WRITE:   fsm <= `STATE_FETCH;
            `STATE_EXECUTE:     fsm <= `STATE_ALU_WB;
            `STATE_ALU_WB:      fsm <= `STATE_FETCH;
            `STATE_BRANCH:      fsm <= `STATE_FETCH;
            `STATE_JUMP:        fsm <= `STATE_FETCH;
            default:            fsm <= `STATE_FETCH;
        endcase
    end
    
    //----------------------------------------------------
    // 控制信号组合逻辑
    //----------------------------------------------------
    assign pcwr = fs0 | (beq & fs8 & ALU_Zero) | ((jal | j) & fs9) | (jr & fs7);
    assign IRWrite = fs0;
    
    // 使能信号
    assign we       = (sw | sb) & fs5;
    assign RegWrite = (fs4 & (lw | lb)) | 
                      (fs7 & (addu | subu | ori | lui | addi | addiu | slt)) | 
                      (fs9 & jal);
    
    // 一些自定义使能（可根据具体数据通路结构调整或移除）
    assign addien = addi & !fs0;
    assign slt_en = slt  & !fs0;
    assign sb_en  = sb   & !fs0;
    assign lb_en  = lb   & !fs0;

    // 多路选择器控制信号
    assign alu_sel      = (ori | lw | lb | sb | sw | lui | addi | addiu) & fs1; // ALU第二操作数选择立即数
    assign reg_sel      = (jal)                                                   ? `REG_DEST_LINK :
                          (addu | subu | slt)                                     ? `REG_DEST_RD :
                          (ori | lui | addi | addiu | lw | lb)                    ? `REG_DEST_RT :
                          2'bxx; // Default case for don't care

    assign ALUOp        = (subu | beq | slt)               ? `ALUOP_SUB :
                          (ori | lui)                      ? `ALUOP_OR  :
                          (addu|lw|lb|sb|sw|addi|addiu)    ? `ALUOP_ADD :
                          3'bxxx; // Default case for don't care

    assign WriteBackSel = (lw | lb)                                             ? `WB_SEL_MEM :
                          (jal)                                                 ? `WB_SEL_PC4 :
                          (addu | subu | ori | lui | addi | addiu | slt)        ? `WB_SEL_ALUOUT :
                          2'bxx; // Default case for don't care

    assign PCSrc        = (beq & ALU_Zero & fs8)           ? `PC_SRC_BEQ :
                          ((j | jal) & fs9)                ? `PC_SRC_JUMP :
                          (jr & fs7)                       ? `PC_SRC_JR :
                          `PC_SRC_PC4;

    assign ExtOp        = (ori)                              ? `EXT_OP_ZERO :
                          (lui)                              ? `EXT_OP_LUI  :
                          (lw | lb | sb | sw | addi | addiu) ? `EXT_OP_SIGN :
                          2'bxx; // Default case for don't care

endmodule