/*
 * --------------------------------------------------------------------
 * 模块名称: controller
 * 文件名称: controller.v
 * 描述:     MIPS多周期处理器的FSM控制器。
 * --------------------------------------------------------------------
 */
`include "defines.v"

module controller(
    input clk, rst,
    input [5:0] Opcode, Funct,
    input       ALU_Zero,
    output reg       RegWrite, MemWrite, PCWrite, IRWrite, ExtOp,
    output reg [1:0] PCSrc, ALUSrcA, ALUSrcB, WriteBackSel, GPRWriteAddrSel,
    output reg [3:0] ALUOp
);
    
    reg [3:0] state, next_state;

    always @(posedge clk or posedge rst) begin
        if (rst) state <= `S_FETCH;
        else state <= next_state;
    end

    // 状态转移逻辑
    always @(*) begin
        case (state)
            `S_FETCH: next_state = `S_DECODE;
            `S_DECODE: begin
                case (Opcode)
                    `OP_R_TYPE: begin
                        if (Funct == `FUNCT_JR) next_state = `S_JR_COMP;
                        else next_state = `S_EXECUTE_R;
                    end
                    `OP_LW, `OP_SW: next_state = `S_MEM_ADDR_CALC;
                    `OP_ADDI, `OP_ADDIU, `OP_ORI: next_state = `S_EXECUTE_I;
                    `OP_BEQ: next_state = `S_BRANCH_COMP;
                    `OP_J: next_state = `S_JUMP_COMP;
                    `OP_JAL: next_state = `S_JAL_WB; // JAL has its own WB state
                    default: next_state = `S_FETCH;
                endcase
            end
            `S_MEM_ADDR_CALC: begin
                if (Opcode == `OP_LW) next_state = `S_MEM_READ;
                else next_state = `S_MEM_WRITE;
            end
            `S_EXECUTE_R:     next_state = `S_WB_FROM_ALU_R;
            `S_EXECUTE_I:     next_state = `S_WB_FROM_ALU_I;
            `S_BRANCH_COMP:   next_state = `S_FETCH;
            `S_MEM_READ:      next_state = `S_WB_FROM_MEM;
            `S_MEM_WRITE:     next_state = `S_FETCH;
            `S_WB_FROM_MEM:   next_state = `S_FETCH;
            `S_WB_FROM_ALU_R: next_state = `S_FETCH;
            `S_WB_FROM_ALU_I: next_state = `S_FETCH;
            `S_JUMP_COMP:     next_state = `S_FETCH;
            `S_JAL_WB:        next_state = `S_FETCH; // After JAL writeback, go to fetch
            `S_JR_COMP:       next_state = `S_FETCH;
            default:          next_state = `S_FETCH;
        endcase
    end

    // 输出逻辑
    always @(*) begin
        // --- 设置所有控制信号的默认值 ---
        RegWrite = 1'b0; MemWrite = 1'b0; PCWrite = 1'b0; IRWrite = 1'b0;
        ExtOp = 1'b1; PCSrc = `PC_SRC_ALU; ALUSrcA = 2'b01; ALUSrcB = 2'b00;
        WriteBackSel = 2'b00; GPRWriteAddrSel = 2'b00; ALUOp = `ALU_ADD;

        case (state)
            `S_FETCH: begin
                PCWrite = 1'b1;
                IRWrite = 1'b1;
                PCSrc = `PC_SRC_ALU;
            end
            `S_DECODE: begin
                if (Opcode == `OP_JAL) begin
                    ALUSrcA = 2'b00; // ALU Input A = PC
                    ALUSrcB = 2'b01; // ALU Input B = 4
                    ALUOp   = `ALU_ADD;  // ALU computes PC+4
                end
            end
            `S_MEM_ADDR_CALC: begin
                ALUSrcA = 2'b01; // A = GPR[rs]
                ALUSrcB = 2'b10; // B = SignExtImm
                ALUOp = `ALU_ADD;
            end
            `S_EXECUTE_R: begin
                ALUSrcA = 2'b01; // A = GPR[rs]
                ALUSrcB = 2'b00; // B = GPR[rt]
                case (Funct)
                    `FUNCT_ADDU: ALUOp = `ALU_ADD;
                    `FUNCT_SUBU: ALUOp = `ALU_SUB;
                    `FUNCT_SLT:  ALUOp = `ALU_SLT;
                endcase
            end
            `S_EXECUTE_I: begin
                ALUSrcA = 2'b01;
                ALUSrcB = 2'b10;
                case (Opcode)
                    `OP_ADDI, `OP_ADDIU: ALUOp = `ALU_ADD;
                    `OP_ORI: begin ALUOp = `ALU_OR; ExtOp = 1'b0; end
                endcase
            end
            `S_BRANCH_COMP: begin
                ALUSrcA = 2'b01;
                ALUSrcB = 2'b00;
                ALUOp = `ALU_SUB;
                if (ALU_Zero) begin
                    PCWrite = 1'b1;
                    PCSrc = `PC_SRC_BRANCH;
                end
            end
            `S_MEM_READ:      {MemWrite} = {1'b0};
            `S_MEM_WRITE:     {MemWrite} = {1'b1};
            `S_WB_FROM_MEM:   {RegWrite, WriteBackSel, GPRWriteAddrSel} = {1'b1, 2'b01, 2'b00};
            `S_WB_FROM_ALU_R: {RegWrite, WriteBackSel, GPRWriteAddrSel} = {1'b1, 2'b00, 2'b01};
            `S_WB_FROM_ALU_I: {RegWrite, WriteBackSel, GPRWriteAddrSel} = {1'b1, 2'b00, 2'b00};
            `S_JUMP_COMP:     {PCWrite, PCSrc} = {1'b1, `PC_SRC_JUMP};
            `S_JAL_WB: begin
                // Write $ra from ALUOut, and update PC to jump target.
                RegWrite = 1'b1;
                WriteBackSel = 2'b00; // Data to write comes from ALUOut (which holds PC+4)
                GPRWriteAddrSel = 2'b10; // Write to $ra ($31)
                
                PCWrite = 1'b1; // Jump!
                PCSrc = `PC_SRC_JUMP;
            end
            `S_JR_COMP:       {PCWrite, PCSrc} = {1'b1, `PC_SRC_JR};
        endcase
    end
endmodule