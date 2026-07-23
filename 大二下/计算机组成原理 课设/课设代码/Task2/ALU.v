/*
 * 模块名称: ALU (Arithmetic Logic Unit)
 * 文件名称: ALU.v
 * 描述:     根据 MIPS-Lite2 指令集要求，实现所有必需的算术和逻辑运算。
 * - 支持 addu, subu, ori, slt, addi 等指令。
 */

module ALU(A, B, ALU_op, zero, alu_out, overflow, slt, addi);
  input signed [31:0] A, B;		//参与运算的输入数据A、B
  input addi, slt;		//是否为addi或slt指令
  input [2:0]ALU_op;		//ALU控制信号，选择运算的类型
  output zero, overflow;
  output [31:0]alu_out;
  
  wire [31:0]tmp;
  // srav：将一个寄存器中的数值向右移动指定的位数，并在左边空出的高位上填充原始数值的符号位
  assign tmp = (ALU_op==0) ? A + B : (ALU_op==1) ? A - B : (ALU_op==2) ? A | B : (ALU_op==3)? (B >>> A[4:0]) :0;
  assign alu_out = (slt) ? {31'b0, tmp[31]} : tmp;    // 如果是slt指令则返回slt标志，否则返回计算结果
  assign overflow = (addi && ((~A[31]&~B[31]&tmp[31]) | (A[31]&B[31]&~tmp[31]))) ? 1 : 0;
  // 当两个符号相同的数相加，其结果的符号却与加数的符号相反
  assign zero = (tmp == 0);
endmodule
  