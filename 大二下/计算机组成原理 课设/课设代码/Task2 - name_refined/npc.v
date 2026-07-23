/*
 * --------------------------------------------------------------------
 * 模块名称: npc (Next PC Calculation Unit)
 * 描述:     根据当前PC、指令和控制信号，计算下一条指令的地址。
 * --------------------------------------------------------------------
 */

module npc(PC, Instr_25_0, register, PCSrc, zero, NPC, pc_add4);
	  input [31:0]PC, register;  //当前地址、jr的寄存器输入
	  input [25:0]Instr_25_0;		//26位立即数
	  input [1:0] PCSrc;
	  input zero;
	  output [31:0]NPC, pc_add4;
	  
	  wire [31:0]tmp0, tmp1, tmp2, tmp3;

	  assign tmp0 = PC + 4;
	  assign tmp1 = {{14{Instr_25_0[15]}}, Instr_25_0[15:0], 2'b00} + PC;
	  assign tmp2 = {PC[31:28], Instr_25_0, 2'b00};
	  assign tmp3 = register;
	  
	  assign NPC = (PCSrc == 3) ? tmp3 : (PCSrc == 2) ? tmp2 : (PCSrc == 1 && zero) ? tmp1 : tmp0;
	  assign pc_add4 = PC;
endmodule
  