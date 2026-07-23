/*
 * 模块名称: ext (Extension Unit)
 * 文件名称: ext.v
 * 描述:     根据控制信号，对16位立即数进行符号扩展或零扩展，生成32位数据。
 * - 符号扩展: 用于 addi, lw, sw, beq 等指令。
 * - 零扩展:  用于 ori 等逻辑指令。
 */

module ext(imm16, imm32, ExtOp);  //将16位立即数实现零扩展、符号扩展、低位补0而扩展为32位
  input[15:0]imm16;   //16位立即数
  input[1:0]ExtOp;	 //符号扩展控制信号
  output[31:0]imm32;	 //符号扩展输出结果
  assign imm32 = (ExtOp==0) ? {16'h0000, imm16} : (ExtOp==1) ? {{16{imm16[15]}}, imm16} : {imm16, 16'h0000};
endmodule