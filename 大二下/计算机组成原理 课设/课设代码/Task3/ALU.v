module ALU(A, B, ALU_Op, zero, overflow, result);
	input [31:0] A, B;
	input [2:0] ALU_Op;
	output zero;
	output overflow;
	output [31:0] result;
	
	reg [31:0] dout;
	assign zero = (result == 0);
	assign overflow = (ALU_Op == 3'b100) && ((A[31] == B[31]) && (result[31] != A[31]));
	assign result = dout;
	
	always @ (*)
		case(ALU_Op)
			3'b000:	dout = A + B;
			3'b001:	dout = A - B;
			3'b010:	dout = A | B;
			3'b011:	dout = ($signed(A) < $signed(B)) ? 32'b1 : 32'b0;
			3'b100:	dout = A + B;
			default:	dout = 32'b0;
		endcase

endmodule


  
