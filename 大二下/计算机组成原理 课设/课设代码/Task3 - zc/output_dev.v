module output_dev(clk, en, addr, din, dout);
  input clk, en;
  input [5:2] addr;
  input [31:0] din;
  output [31:0] dout;
  
  reg [31:0] preData, curData;
  
  initial begin
    preData = 0; curData = 0;
  end
  
  always@(posedge clk)  begin
    if(en)
      case(addr)
        4'b1000:
          preData <= din;
        4'b1001:
          curData <= din;
        default:
          $display("Illegal addr");
      endcase
  end
  
  assign dout = (addr == 4'b1000) ? preData : (addr == 4'b1001) ? curData : 32'bz;
  
endmodule