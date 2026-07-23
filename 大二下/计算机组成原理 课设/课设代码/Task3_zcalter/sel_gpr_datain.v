module sel_gpr_datain(WDsel, aluout, D_in, pc_4, gpr_datain, cp0_dout);
	input [2:0] WDsel;
	input [31:0] aluout, D_in, pc_4, cp0_dout;
	output reg [31:0] gpr_datain;
  
	always@(*)
		case(WDsel)
			2'b00:begin
				gpr_datain = aluout;//alu输出
				$display("Choose GPR.datain: aluout");
				$display(" ");
			end
			2'b01:begin
				gpr_datain = D_in;// DM取出
				$display("Choose GPR.datain: D_in");
				$display(" ");
			end
			2'b10:begin
				gpr_datain = pc_4;//jal指令，pc_plus4存入31号寄存器
				$display("Choose GPR.datain: npc.pc+4");
				$display(" ");
			end
			2'b11:begin
				gpr_datain = 32'b1;//溢出，1写入30号寄存器
				$display("Choose GPR.datain: 1 as overflow flag");
				$display(" ");
			end
			3'b100:
				gpr_datain = cp0_dout;
			default:  gpr_datain =0;
		endcase
endmodule