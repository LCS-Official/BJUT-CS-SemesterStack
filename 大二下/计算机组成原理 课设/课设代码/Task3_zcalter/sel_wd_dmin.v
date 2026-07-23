module sel_wd_dmin(addr, device_out, drout, dmin);
  input [31:0] drout, device_out, addr;
  output [31:0] dmin;
  assign dmin = (addr[15:8] == 8'h7f) ? device_out : drout;
endmodule
