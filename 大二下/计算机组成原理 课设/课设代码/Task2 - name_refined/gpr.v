/*
 * 模块名称: gpr (General Purpose Registers)
 * 文件名称: gpr.v
 * 描述: MIPS通用寄存器堆。
 */

module gpr(clk, rst, rs, rt, rw, wd, RegWrite, busA, busB, addi_overflow);
	input clk, rst, RegWrite;	//时钟、复位、写信号使能
	input [4:0] rs, rt, rw;  	//寄存器号
	input [31:0] wd;				//写入的内容
	output [31:0] busA, busB;	//rs、rt寄存器内容
	input addi_overflow;			//溢出信号
	reg [31:0] registers[31:0];
  
	integer i = 0;
	always @ (posedge clk, posedge rst) begin
		if (rst) begin
			for (i = 0; i < 32; i = i + 1) begin
				case(i)
					28:registers[i]<=32'h0000_1800;		// 全局寄存器
					29:registers[i]<=32'h0000_2ffc;		// 堆栈寄存器
					default registers[i]<=32'h0000_0000; // 32个寄存器赋初值
				endcase
			end
		end
		else begin
			if (addi_overflow && RegWrite)    //addi指令溢出
				registers[30] = 1;
			if (RegWrite && (rw != 5'b0))
				registers[rw] <= wd;
		end

	end
    assign busA = (rs == 5'b0) ? 32'b0 : registers[rs];
    assign busB = (rt == 5'b0) ? 32'b0 : registers[rt];
  
endmodule