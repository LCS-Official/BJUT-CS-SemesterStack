module sel_wd_dmin(addr,dev_out, drout, dmin);
  input [31:0] drout, dev_out, addr;
  output [31:0] dmin;
  assign dmin = (addr[15:8] == 8'h7f) ? dev_out : drout;//选输入外设的还是dm的 在gprdatain的sel之前
endmodule
