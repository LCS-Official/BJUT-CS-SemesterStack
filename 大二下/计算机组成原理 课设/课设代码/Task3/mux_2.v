module mux_2(WD_sel, aluo, DM_out, pc_4, m2out, cp0out);
  input [2:0] WD_sel;
  input [31:0] aluo, DM_out, pc_4, cp0out;
  output reg [31:0] m2out;
  
  always@(*)
  begin
  m2out = 0;
    case(WD_sel)
        3'b00:
          m2out = aluo;
        3'b01:
          m2out = DM_out;
        3'b10:
          m2out = pc_4;
        3'b11:
          m2out = 32'b1;
        3'b100:
          m2out = cp0out;
        default:;
    endcase
	 end
endmodule


//选择写回数据（ALU 结果 / DM 数据 / PC+4/CP0 数据）