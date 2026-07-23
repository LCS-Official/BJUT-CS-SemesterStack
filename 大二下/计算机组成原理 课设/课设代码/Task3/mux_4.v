module mux_4(DR_out, prrd, m4out, addr);
  input [31:0] DR_out, prrd, addr;
  output [31:0] m4out;
  
  assign m4out = (addr[15:8] == 8'h7f) ? prrd : DR_out;
endmodule
//选择数据存储器读数据（设备数据 / 寄存器数据）