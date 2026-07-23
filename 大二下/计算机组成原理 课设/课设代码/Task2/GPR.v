/*
 * 模块名称: GPR (General Purpose Registers)
 * 文件名称: GPR.v
 * 描述: MIPS通用寄存器堆。
 */
module GPR(clk, reset, rs, rt, rw, wd, regwrite, busA, busB, addi_overflow);
  input clk, reset, regwrite;	//时钟、复位、写信号使能
  input [4:0] rs, rt, rw;  	//寄存器号
  input [31:0] wd;				//写入的内容
  output [31:0] busA, busB;	//rs、rt寄存器内容
  input addi_overflow;			//溢出信号
  reg [31:0] registers[31:0];
  integer i;
  
  always @ (posedge clk or posedge reset) begin

    if (reset)
      for (i = 0; i < 32; i = i + 1)
        case(i)
				28:registers[i]<=32'h0000_1800;		//全局寄存器
				29:registers[i]<=32'h0000_2ffc;		//堆栈寄存器
				default: registers[i]<=32'h0000_0000; //32个寄存器赋初值
		  endcase
    else
      if (addi_overflow && regwrite)    //addi指令溢出
        registers[30] <= 1;
      else if (regwrite && rw)
        registers[rw] <= wd;
  end
  
  assign busA = registers[rs];
  assign busB = registers[rt];
endmodule