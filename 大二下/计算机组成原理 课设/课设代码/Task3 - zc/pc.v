module pc(clk, pcin, pcout,pcwr);
  input [31:0] pcin;
  input clk,pcwr;
  output reg [31:0] pcout;
  
  always@(posedge clk)
    if(pcwr)
      pcout <= pcin;

endmodule
