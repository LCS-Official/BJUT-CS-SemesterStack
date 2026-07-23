module PC(clk, PC_wr, pcin, pcout);
	input clk, PC_wr;
	input [31:0] pcin;
	output reg [31:0] pcout;
  
	always @ (posedge clk)
		if(PC_wr)
			pcout <= pcin;

endmodule