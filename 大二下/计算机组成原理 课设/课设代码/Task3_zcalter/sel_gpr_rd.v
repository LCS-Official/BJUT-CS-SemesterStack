module sel_gpr_rd(
  input [1:0] sel_gpr_rd,
  input [4:0] rt, 
  input [4:0] rd,
  output reg  [4:0] gpr_rd
  );
  
	always@(*) begin
		case(sel_gpr_rd)
			2'b00:begin
				gpr_rd = rt;
				$display("Choose GPR.rd: rt");
			end
			2'b01:begin
				gpr_rd = rd;
				$display("Choose GPR.rd: rd");
			end
			2'b10:begin
				gpr_rd = 5'b11111;
				$display("Choose GPR.rd: reg 31 for return address");
			end
			2'b11:begin
				gpr_rd = 5'b11110;//溢出 30号寄存器
				$display("Choose GPR.rd: reg 30 for overflow");
			end
			default: gpr_rd = 0;
		endcase
	end
endmodule
