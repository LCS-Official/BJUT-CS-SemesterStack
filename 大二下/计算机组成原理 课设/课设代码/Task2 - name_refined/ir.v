module ir(clk, ins, rs, rt, rd, func, OpCode, imm26, IRWrite); //将im输出存入寄存器
	input [31:0] ins;				//指令内容
	input clk, IRWrite;			
	output reg[5:0] func, OpCode;
	output reg[4:0] rs, rt, rd;
	output reg[25:0] imm26;		//26位立即数
  
	always @ (posedge clk) begin
		if (IRWrite) begin
			func = ins[5:0];
			OpCode = ins[31:26];
			rs = ins[25:21];
			rt = ins[20:16];
			rd = ins[15:11];
			imm26 = ins[25:0];
		end
	end
endmodule