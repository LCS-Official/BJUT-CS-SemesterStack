/*
 * 模块名称: alu (Arithmetic Logic Unit)
 * 文件名称: alu.v
 * 描述:     根据 MIPS-Lite1 指令集要求，实现所有必需的算术和逻辑运算。
 * - 支持 addu, subu, ori, slt, addi 等指令。
 * - 为 beq 指令提供 Zero 标志位输出。
 * - 为 addi 指令提供溢出检测标志位输出。
 */

`include "defines.v" // 引入包含操作码定义的头文件

module alu(
    input  [31:0] A,         // 输入操作数 A
    input  [31:0] B,         // 输入操作数 B
    input  [3:0]  ALUOp,     // 来自控制器的4位操作码，指示执行何种运算
    output reg [31:0] Result,  // 32位运算结果
    output            Zero,      // 零标志位输出 (当 Result 为0时为1)
    output reg        Overflow   // 溢出标志位 (仅用于 addi)
);

    // Zero 标志位的逻辑：当 Result 等于0时，Zero 为1
    assign Zero = (Result == 32'b0);

    // 主体逻辑：使用 always 块描述组合逻辑
    always @(*) begin
        // 默认为不溢出
        Overflow = 1'b0;

        case (ALUOp)
            // 加法 (用于 addu, addiu, lw, sw)
            `ALU_ADD: Result = A + B;

            // 减法 (用于 subu, beq)
            `ALU_SUB: Result = A - B;

            // 或运算 (用于 ori)
            `ALU_OR:  Result = A | B;

            // 有符号小于则置1 (用于 slt)
            // 使用 $signed() 将操作数视为有符号数进行比较
				`ALU_SLT: Result = ($signed(A) < $signed(B)) ? 32'd1 : 32'd0;
				
				`ALU_SLL: Result = A << B; // A是寄存器的值, B是shamt的值

            // 带溢出检测的加法 (用于 addi)
            `ALU_ADDI: begin
                Result = A + B;
                // 溢出检测逻辑:
                // 当两个正数相加得到负数，或两个负数相加得到正数时，发生溢出。
                // 即 A 和 B 的符号位相同，但与 Result 的符号位不同。
                if (A[31] == B[31] && Result[31] != A[31]) begin
                    Overflow = 1'b1;
                end else begin
                    Overflow = 1'b0;
                end
            end

            // 默认情况，输出为0，防止产生锁存器
            default: Result = 32'b0;
        endcase
    end

endmodule