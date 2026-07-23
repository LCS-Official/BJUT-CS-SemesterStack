module mips(clk, rst, switch_in) ; 
	input clk; 
	input rst;
	input [31:0] switch_in;
	
	wire [31:0] PC, NPC, bus_a, Instr, pc_plus4, gpr_datain, alu_out, d_out, bus_b, EXTOut, ALU_B;
	wire [1:0] NPCOp,GPRSel,ExtOp;
	wire zero, BSel, GPRWr, overflow, We; 

	wire [4:0] gpr_wraddr;
	
	wire [2:0] ALUOp;
	
	wire IRWr, PCWr, lb_sign, sb_sign, IntPc,
			 EX_Lv_Clr, // 异常级别清除
			 bridge_Wren, 
			 dev0_Wren, dev2_Wren, // 设备0/2写使能
			 PauseReq, // 中断请求
			 cp0_Wren, 
			 EX_Lv_Set, // 异常级别设置 
			 StopReq; // 最终中断请求

	wire [31:0] aluout_tmp, ar_out, BROut, dr_out, IROut, EX_cnt, // 异常程序计数器
	  CPU_RD, // 从桥读入处理器的数据
	  dev0_rd, dev2_rd, dev_wd, 
	  D_in, // 写回GPR的数据
	  cp0_dout, switch_out;

	wire[5:0] HWInt;

	wire[2:0] WDsel;

	wire[3:0] dev_addr;
	
	switch Switch(switch_in, switch_out); // 输入设备：32位思维驰

	bridge Bridge(aluout_tmp, BROut, CPU_RD, dev0_rd, switch_out, dev2_rd, dev_wd, dev_addr, bridge_Wren, dev0_Wren, dev2_Wren, HWInt, PauseReq, alt_sign, Ctlr_sign);

	cp0 CP0(PC, BROut, HWInt, IROut[15:11], cp0_Wren, EX_Lv_Set, EX_Lv_Clr, clk, rst, StopReq, EX_cnt, cp0_dout); // 协处理器0：处理中断和异常

	output_dev Output_Dev(clk, rst, dev2_Wren, dev_addr, dev_wd, dev2_rd);  // 输出设备，没加入复位

	timer Timer(clk, rst, dev_addr, dev0_Wren, dev_wd, PauseReq, alt_sign, dev0_rd); // 定时器设备

	controller Controller(IROut[31:26], IROut[5:0], ALUOp, GPRSel, GPRWr, ExtOp, We, WDsel, NPCOp, BSel, overflow, clk, rst, PCWr, IRWr, lb_sign, sb_sign, zero, StopReq, EX_Lv_Set, EX_Lv_Clr, cp0_Wren, bridge_Wren, IntPc, IROut[25:21], Ctlr_sign);

	sel_wd_dmin Selwd_dmin(aluout_tmp, CPU_RD, dr_out, D_in); // 选择写回数据是来自内存还是外设/ALU

	pc PC1(clk, rst, PCWr, NPC, PC);
	  
	npc NPC1(PC, bus_a, NPCOp, zero, IROut[25:0], NPC, pc_plus4, rst, IntPc, EX_cnt, EX_Lv_Clr);

	im_1k IM(PC[9:0], Instr); // 8KB
	dm_1k DM(aluout_tmp[9:0], bus_b, We, clk, d_out,lb_sign, sb_sign); // 12KB
	  
	sel_gpr_rd GPR_rdsel(GPRSel, IROut[20:16], IROut[15:11], gpr_wraddr); // 选择GPR写地址 (rt或rd)
	  
	sel_gpr_datain GPR_detainsel(WDsel, alu_out, D_in, pc_plus4, gpr_datain, cp0_dout); // 选择写入GPR的数据
	  
	sel_alu_b ALU_selb(BSel, BROut, EXTOut, ALU_B); // 选择ALU的B操作数
	  
	gpr GPR(clk, rst, GPRWr, gpr_wraddr, gpr_datain, IROut[25:21], IROut[20:16], bus_a, bus_b, overflow);
	  
	ext EXT(IROut[15:0], ExtOp, EXTOut);
	  
	alu ALU(ar_out, ALU_B, ALUOp, zero, overflow, alu_out);

	aluout ALUOut(clk, alu_out, aluout_tmp);

	// ALU操作数A、B的锁存器
	ar AR(clk, bus_a, ar_out); 
	br BR (clk, bus_b, BROut);

	dr DR(clk, d_out, dr_out); // 内存读出数据的锁存器
	ir IR(IRWr, clk, Instr, IROut);

endmodule