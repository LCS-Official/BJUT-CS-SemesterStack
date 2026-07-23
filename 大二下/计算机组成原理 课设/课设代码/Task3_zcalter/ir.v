module ir(IRWr,clk,Instr,irout);
    input clk, IRWr;
    input [31:0] Instr;
    output reg [31:0] irout;
    always@(posedge clk)
		if(IRWr) irout <= Instr;
		else $display("无法写入IR");
endmodule