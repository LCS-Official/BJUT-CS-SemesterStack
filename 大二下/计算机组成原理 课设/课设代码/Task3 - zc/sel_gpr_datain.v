module sel_gpr_datain(sel_gpr_datain, aluout, dmout, pc_4, gpr_datain,cp0out);
  input [2:0] sel_gpr_datain;
  input [31:0] aluout, dmout, pc_4,cp0out;
  output reg [31:0] gpr_datain;
  
  always@(sel_gpr_datain, aluout, dmout, pc_4,cp0out)
    case(sel_gpr_datain)
        2'b00:begin
          gpr_datain = aluout;//alu输出
          $display("Choose GPR.datain: aluout");
          $display(" ");
        end
        2'b01:begin
          gpr_datain = dmout;//dm取出的
          $display("Choose GPR.datain: dmout");
          $display(" ");
        end
        2'b10:begin
          gpr_datain = pc_4;//jal pc+存入31号寄存器
          $display("Choose GPR.datain: npc.pc+4");
          $display(" ");
        end
        2'b11:begin
          gpr_datain = 32'b1;//溢出 写入30号寄存器
          $display("Choose GPR.datain: 1 as overflow's flag");
          $display(" ");
        end
        3'b100:
          gpr_datain = cp0out;
        default:  gpr_datain =0;
    endcase
endmodule