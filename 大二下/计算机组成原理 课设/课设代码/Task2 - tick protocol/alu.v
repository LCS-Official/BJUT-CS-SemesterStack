// alu.v
`include "defines.v"

module alu(
    input [31:0] a,
    input [31:0] b,
    input [3:0] alu_op,
    output reg [31:0] result,
    output reg zero,
    output reg overflow // 特别为 addi 指令设计
);
    
    always @(*) begin
        overflow = 1'b0; // 默认无溢出
        case (alu_op)
            `ALU_ADD: result = a + b;
            `ALU_SUB: result = a - b;
            `ALU_OR:  result = a | b;
            `ALU_SLT: result = (a < b) ? 32'd1 : 32'd0;
            `ALU_LUI: result = {b[15:0], 16'b0};
            default: result = 32'hxxxxxxxx;
        endcase
		  
		  zero = (result == 32'b0);

        // 处理 addi 的溢出检测
        // 溢出条件: 两个正数相加得负数，或两个负数相加得正数
        if (alu_op == `ALU_ADD) begin
            if (a[31] == b[31] && a[31] != result[31]) begin
                overflow = 1'b1;
            end
        end
    end

endmodule