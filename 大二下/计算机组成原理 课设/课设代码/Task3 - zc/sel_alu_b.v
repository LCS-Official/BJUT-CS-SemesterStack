module sel_alu_b(sel_alu_b, bout, imm32, alu_b);
  input sel_alu_b;
  input [31:0] bout, imm32;
  output reg [31:0] alu_b;
  
  always@(sel_alu_b, bout, imm32)
    case(sel_alu_b)
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
