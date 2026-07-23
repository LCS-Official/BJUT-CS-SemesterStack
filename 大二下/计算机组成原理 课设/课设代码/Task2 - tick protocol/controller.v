// controller.v
`include "defines.v"

module controller(
    input clk,
    input rst,
    input [5:0] op,
    input [5:0] funct,
    input zero,
    input overflow,

    // Control signals to Datapath
    output reg pc_write,
    output reg ir_write,
    output reg reg_write,
    output reg mem_read,
    output reg mem_write,
    output reg sign_ext_en,
    output reg [1:0] reg_dst,
    output reg [1:0] alu_src_a,
    output reg [1:0] alu_src_b,
    output reg [1:0] mem_to_reg,
    output reg [1:0] next_pc_sel,
    output reg [3:0] alu_op,
    output reg [1:0] dm_data_size
);

    reg [3:0] current_state, next_state;

    // FSM State Register
    always @(posedge clk or posedge rst) begin
        if (rst)
            current_state <= `S_FETCH;
        else
            current_state <= next_state;
    end
    
    // FSM Next State Logic
    always @(*) begin
        case (current_state)
            `S_FETCH: next_state = `S_DECODE;
            `S_DECODE: begin
                case (op)
                    `OP_RTYPE: begin
                        case (funct)
                            `FUNCT_JR: next_state = `S_JR;
                            default: next_state = `S_EXEC_R;
                        endcase
                    end
                    `OP_ADDI, `OP_ADDIU, `OP_ORI, `OP_LUI: next_state = `S_EXEC_I_ALU;
                    `OP_LW, `OP_LB: next_state = `S_EXEC_MEM;
                    `OP_SW, `OP_SB: next_state = `S_EXEC_MEM;
                    `OP_BEQ: next_state = `S_BEQ;
                    `OP_J, `OP_JAL: next_state = `S_JUMP;
                    default: next_state = `S_FETCH; // Invalid instruction
                endcase
            end
            `S_EXEC_R: next_state = `S_WB_REG;
            `S_EXEC_I_ALU: begin
                 if (op == `OP_ADDI && overflow) next_state = `S_ADDI_OVF;
                 else next_state = `S_WB_REG;
            end
            `S_ADDI_OVF: next_state = `S_WB_REG; // After handling overflow, proceed to write back addi result
            `S_EXEC_MEM: begin
                if (op == `OP_LW || op == `OP_LB) next_state = `S_MEM_READ;
                else next_state = `S_MEM_WRITE; // SW, SB
            end
            `S_MEM_READ: next_state = `S_WB_MEM;
            `S_MEM_WRITE: next_state = `S_FETCH;
            `S_WB_REG: next_state = `S_FETCH;
            `S_WB_MEM: next_state = `S_FETCH;
            `S_BEQ: next_state = `S_FETCH;
            `S_JUMP: next_state = `S_FETCH;
            `S_JR: next_state = `S_FETCH;
            default: next_state = `S_FETCH;
        endcase
    end

    // FSM Output Logic (Control Signal Generation)
    always @(*) begin
        // Default values
        pc_write = 0; ir_write = 0; reg_write = 0; mem_read = 0; mem_write = 0;
        sign_ext_en = 0; reg_dst = 2'bxx; alu_src_a = 2'bxx; alu_src_b = 2'bxx;
        mem_to_reg = 2'bxx; next_pc_sel = 2'b00; alu_op = 4'bxxxx; dm_data_size = 2'bxx;

        case (current_state)
            `S_FETCH: begin // 取指
					 ir_write = 1;
                pc_write = 1;
                alu_src_a = 2'b00; // PC
                alu_src_b = 2'b01; // 4
                alu_op = `ALU_ADD;
                next_pc_sel = 2'b00; // PC = PC+4
            end
            `S_DECODE: begin // 译码
                alu_src_a = 2'b00; // PC
                alu_src_b = 2'b10; // imm
                alu_op = `ALU_ADD; // For branch address calculation
            end
            `S_EXEC_R: begin // addu, subu, slt
                alu_src_a = 2'b01; // A reg
                alu_src_b = 2'b00; // B reg
					 if (funct == `FUNCT_ADDU) alu_op = `ALU_ADD;
					 else if (funct == `FUNCT_SUBU) alu_op = `ALU_SUB;
					 else if (funct == `FUNCT_SLT) alu_op = `ALU_SLT;
				end
            `S_EXEC_I_ALU: begin // addi, addiu, ori, lui
                alu_src_a = 2'b01; // A reg
                alu_src_b = 2'b10; // imm
                sign_ext_en = (op == `OP_ADDI || op == `OP_ADDIU);
                if (op == `OP_ORI) alu_op = `ALU_OR;
                else if (op == `OP_LUI) alu_op = `ALU_LUI;
                else alu_op = `ALU_ADD; // ADDI, ADDIU
            end
            `S_ADDI_OVF: begin // addi 溢出写 $30
                reg_write = 1;
                reg_dst = 2'b11; // write to $30
                mem_to_reg = 2'b11; // data is overflow bit
            end
            `S_EXEC_MEM: begin // lw, sw, lb, sb
                alu_src_a = 2'b01; // A reg
                alu_src_b = 2'b10; // imm
                sign_ext_en = 1;
                alu_op = `ALU_ADD;
            end
            `S_MEM_READ: begin // lw, lb
                mem_read = 1;
                dm_data_size = (op == `OP_LW) ? 2'b10 : 2'b00;
            end
            `S_MEM_WRITE: begin // sw, sb
                mem_write = 1;
                dm_data_size = (op == `OP_SW) ? 2'b10 : 2'b00;
            end
            `S_WB_REG: begin // 写回 (来自ALU)
                reg_write = 1;
                reg_dst = (op == `OP_RTYPE) ? 2'b01 : 2'b00; // R-type -> rd, I-type -> rt
                mem_to_reg = 2'b00; // from ALU_out
            end
            `S_WB_MEM: begin // 写回 (来自DM)
                reg_write = 1;
                reg_dst = 2'b00; // rt
                mem_to_reg = 2'b01; // from MDR
            end
            `S_BEQ: begin
                alu_src_a = 2'b01; alu_src_b = 2'b00; alu_op = `ALU_SUB;
                if (zero) begin
                    pc_write = 1;
                    next_pc_sel = 2'b01; // Branch
                end
            end
            `S_JUMP: begin
                pc_write = 1;
                next_pc_sel = 2'b10; // Jump
                if (op == `OP_JAL) begin // jal
                    reg_write = 1;
                    reg_dst = 2'b10; // $ra
                    mem_to_reg = 2'b10; // PC+4
                end
            end
            `S_JR: begin
                pc_write = 1;
                next_pc_sel = 2'b11; // from register A
            end
        endcase
    end
endmodule