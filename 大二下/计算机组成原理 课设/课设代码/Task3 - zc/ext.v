//same
module ext(imm16, extop, out);
  input [15:0] imm16;//指令低16位
  input [1:0] extop;//00 无符号 01符号 10高位复制
  output reg [31:0] out;
  
  always@(*)  begin
    case(extop)
      2'b00: out = {16'b0, imm16};
      2'b01: out = {{16{imm16[15]}}, imm16}; 
      2'b10: out = {imm16, 16'b0};
      default: out = 32'b0;
    endcase
  end

endmodule