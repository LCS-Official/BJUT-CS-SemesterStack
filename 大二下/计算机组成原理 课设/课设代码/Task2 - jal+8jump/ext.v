/*
 * 模块名称: ext (Extension Unit)
 * 文件名称: ext.v
 * 描述:     根据控制信号，对16位立即数进行符号扩展或零扩展，生成32位数据。
 * - 符号扩展: 用于 addi, lw, sw, beq 等指令。
 * - 零扩展:  用于 ori 等逻辑指令。
 */
module ext (
    input  [15:0] Imm16,   // 来自指令的16位立即数
    input         ExtOp,   // 扩展操作控制信号 (1:符号扩展, 0:零扩展)
    output [31:0] Imm32    // 扩展后的32位立即数
);

    // 使用 assign 和条件运算符实现扩展逻辑，简洁高效。
    assign Imm32 = ExtOp ? {{16{Imm16[15]}}, Imm16} : {16'h0, Imm16};
	 
endmodule