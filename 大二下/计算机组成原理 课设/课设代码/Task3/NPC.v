module NPC(PC, rd1, NPC_Op, zero, imm26, NPC, PC_plus4, rst, epc, ERET, IntReq);
	input [25:0] imm26;
	input [31:0] PC;
	input [31:0] rd1;
	input zero, rst;
	input [1:0] NPC_Op;
	output reg [31:0] NPC;
	output [31:0] PC_plus4;
	input [31:0] epc;
	input ERET, IntReq;
  
	wire [15:0] imm16;
	reg [31:0] pcnew;
	
	assign PC_plus4 = PC;
	assign imm16 = imm26[15:0];

	initial
		NPC = 32'h0000_3000;
  
	always @ (*)
		if(rst)
			NPC = 32'h0000_3000;
		else
			if(ERET)
				NPC = epc;
			else
				NPC = pcnew;
  
	always @ (*)
		if(IntReq)
			pcnew = 32'h0000_4180;
		else
			case(NPC_Op)
				2'b00: 	pcnew = PC + 4;
				2'b01: 
					if(zero)
						pcnew = PC + {{14{imm16[15]}}, imm16, 2'b00};
					else
						pcnew = PC + 4;
				2'b10:	pcnew = {PC_plus4[31:28], imm26, 2'b00};
				2'b11:	pcnew = rd1;
				default: pcnew = PC + 4;
			endcase

endmodule
