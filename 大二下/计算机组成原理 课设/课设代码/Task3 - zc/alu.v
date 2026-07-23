//same to singlepath
module alu(A, B, aluctr, zero, overflow, out);
  input [31:0] A, B;
  input [2:0] aluctr;
  
  output zero;
  output overflow;//溢出标志位
  output [31:0] out;
  
  
  reg [31:0] dout;
  
  //判断溢出
  wire [32:0] temp;
  assign temp = {A[31], A} + B;
  assign overflow = (aluctr == 3'b100) ? ((A[31]==B[31])&&(temp[32] != temp[31]) ? 1 : 0 ): 0;
  
  always@(*)  begin
    case(aluctr)//00 加 01 减 10 或 11 小于置位 100 addi的加 溢出判断
      3'b000: dout = A + B;
      3'b001: dout = A - B;
      3'b010: dout = A | B;
      //有符号数比较
      3'b011: begin 
        dout = ($signed(A) < $signed(B)) ? 32'b1 : 32'b0;//slt
        if(dout==32'b1) $display("In alu: slt,true");
        else $display("In alu: slt,false");
      end
      3'b100: dout = A + B; 
      default: dout = 32'b0;
    endcase
  end
  
  assign out = dout;
  assign zero = ($signed(A) == $signed(B)) ? 1 : 0;
  
  always@(*)
    if(zero==0) $display("zero==0");
  
endmodule