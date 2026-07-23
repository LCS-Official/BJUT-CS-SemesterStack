module EXT(imm16, ExtOp, imm32);
	input [15:0] imm16;
	input [1:0] ExtOp;
	output reg [31:0] imm32;
  
	always @ (*)
		case(ExtOp)
			2'b00:	imm32 = {16'b0, imm16};  
			2'b01:	imm32 = {{16{imm16[15]}}, imm16};
			2'b10:	imm32 = {imm16, 16'b0};
			default:	imm32 = 32'b0;
		endcase

endmodule

