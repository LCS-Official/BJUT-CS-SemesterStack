/*
 * 模块名称: controller
 * 文件名称: controller.v
 * 描述:     MIPS单周期处理器的控制器。
 */
`include "defines.v"

module controller(
    input  [31:0] Instr,
    input         ALU_Zero,
    input         ALU_Overflow,
	 input         GPR_RD1_Sign, // 接收来自数据通路的符号位
    
    output reg    RegWrite,
    output reg    ExtOp,
    output reg [3:0]  ALUOp,
    output reg [1:0]  PCSrc,
    output reg    RegDst,
    output reg    ALUSrc,
    output reg    MemWrite,
    output reg [1:0] WriteBackSel,
    output reg       JAL_Write,
    output           Ovf_WriteEnable
);

    wire [5:0] opcode = Instr[31:26];
    wire [5:0] funct  = Instr[5:0];
    
    assign Ovf_WriteEnable = (opcode == `OP_ADDI) && ALU_Overflow;

    always @(*) begin
        // --- 默认值 ---
        RegWrite     = 1'b0;
        ExtOp        = 1'b1;
        ALUOp        = `ALU_ADD;
        PCSrc        = `PC_SRC_P4;
        RegDst       = 1'b0;
        ALUSrc       = 1'b0;
        MemWrite     = 1'b0;
        WriteBackSel = `WB_ALU;
        JAL_Write    = 1'b0;

        // --- 根据opcode进行主解码 ---
        case (opcode)
            `OP_R_TYPE: begin 
                RegWrite = 1'b1;
                RegDst   = 1'b1;
                ALUSrc   = 1'b0;
                case (funct)
                    `FUNCT_ADDU: ALUOp = `ALU_ADD;
                    `FUNCT_SUBU: ALUOp = `ALU_SUB;
                    `FUNCT_SLT:  ALUOp = `ALU_SLT;
                    `FUNCT_JR: begin
                        RegWrite = 1'b0;
                        PCSrc = `PC_SRC_JR;
                    end
                    default: ; 
                endcase
            end
            
            `OP_LW: begin
                RegWrite = 1'b1;
                ALUSrc   = 1'b1;
                ExtOp    = 1'b1;
                ALUOp    = `ALU_ADD;
                WriteBackSel = `WB_MEM;
            end

            `OP_SW: begin
                ALUSrc   = 1'b1;
                MemWrite = 1'b1;
                ExtOp    = 1'b1;
                ALUOp    = `ALU_ADD;
            end

            `OP_BEQ: begin
                PCSrc = ALU_Zero ? `PC_SRC_BRANCH : `PC_SRC_P4;
                ExtOp = 1'b1;
                ALUSrc = 1'b0;
                ALUOp = `ALU_SUB;
            end
				
            `OP_BLEZ: begin
                // blez 的 rt 字段必须为0, 假设指令合法
                // 分支条件为 (rs的符号位为1) OR (ALU计算rs-0的结果为0)
                PCSrc = (GPR_RD1_Sign || ALU_Zero) ? 2'b01 : `PC_SRC_P4;
                ExtOp = 1'b1;     // 偏移量需要符号扩展
                ALUSrc = 1'b0;     // ALU 输入是 rs 和 $zero
                ALUOp = `ALU_SUB;  // ALU 执行减法来判断是否为零
            end

            `OP_ORI: begin
                RegWrite = 1'b1;
                ALUSrc   = 1'b1;
                ExtOp    = 1'b0;
                ALUOp    = `ALU_OR;
            end
            
            `OP_ADDI: begin
                RegWrite = ~Ovf_WriteEnable;
                ALUSrc   = 1'b1;
                ExtOp    = 1'b1;
                ALUOp    = `ALU_ADDI;
            end
            
            `OP_ADDIU: begin
                RegWrite = 1'b1;
                ALUSrc   = 1'b1;
                ExtOp    = 1'b1;
                ALUOp    = `ALU_ADD;
            end
            
            `OP_J: begin
                PCSrc = `PC_SRC_JUMP;
            end
            
            `OP_JAL: begin
                RegWrite = 1'b1;
                PCSrc    = `PC_SRC_JUMP;
                WriteBackSel = `WB_PC4;
                JAL_Write = 1'b1;
            end
            
            `OP_LUI: begin
                RegWrite = 1'b1;
                ALUSrc   = 1'b1;
                WriteBackSel = `WB_LUI;
            end
				

            
            default: ; 
        endcase
        
        if (Ovf_WriteEnable) begin
            RegWrite = 1'b1;
        end
    end

endmodule