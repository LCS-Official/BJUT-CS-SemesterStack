module sel_alu_b(
  input BSel,
  input [31:0] bout, 
  input [31:0] imm32,
  output reg [31:0] alu_b
  );
  
	always@(*)
		case(BSel)
			1'b0:begin
				alu_b = bout;
				$display("Choose ALU.B: GPR.busB");
			end
			1'b1:begin
				alu_b = imm32;
				$display("Choose ALU.B: ext.imm");
			end
			default:
				alu_b = 32'b0;
		endcase
endmodule
