module GPR(clk, rst, Reg_Wr, m1out, m2out, rs, rt, busa, busb);
	input clk, rst, Reg_Wr;
	input [31:0] m2out;
	input [4:0] rs, rt, m1out;
	output [31:0] busa, busb;
	reg [31:0] registers [31:0];

	assign busa = registers[rs];
	assign busb = registers[rt];
  
	integer i;
  
	initial
		for(i = 0; i < 32; i = i + 1)
			registers[i] <= 0;
  
	always @ (posedge clk)
		if(rst)
			for(i = 0; i < 32; i = i + 1)
				registers[i] <= 0;
		else
			if(Reg_Wr && m1out != 5'b00000)
				registers[m1out] <= m2out;
endmodule