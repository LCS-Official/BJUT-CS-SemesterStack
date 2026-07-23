module mux_3(B_sel, ALU_B, imm32, m3out);
  input B_sel;
  input [31:0] ALU_B, imm32;
  output reg [31:0] m3out;
  
  always@(B_sel, ALU_B, imm32)
    case(B_sel)
      1'b0:
        m3out = ALU_B;
      1'b1:
        m3out = imm32;
      default:
        m3out = 32'b0;
    endcase
endmodule