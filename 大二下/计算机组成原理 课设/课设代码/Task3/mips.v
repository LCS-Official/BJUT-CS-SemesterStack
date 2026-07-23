module mips(clk, rst, dev1_rd, Data2out, IntReq, cnt);
	input clk;
	input rst;
	input [31:0] dev1_rd;
	output [31:0] Data2out;
	output IntReq;         // 顶层中断输出
	output [31:0] cnt;

	// --- 控制信号 ---
	wire pc_we; 
	wire [1:0] next_pc_op;  // 下一条PC来源操作码
	wire gpr_we; 
	wire [1:0] gpr_dest_sel;
	wire [2:0] gpr_wr_data_sel; 
	wire ir_we; 
	wire mem_we; 
	wire bsel; 
	wire [1:0] ext_op;
	wire [2:0] alu_op;
	wire is_lb;
	wire is_sb;

	// --- 异常与中断相关控制信号 ---
	wire internal_int_req;  // 来自CP0的内部中断请求信号
	wire cp0_we;            // CP0寄存器写使能
	wire set_exl;           // 设置异常等级标志
	wire clear_exl;         // 清除异常等级标志
	wire jump_to_int_vector;// 跳转至中断向量

	// --- 数据通路信号 ---
	wire [31:0] pc_current;      // 当前PC值
	wire [31:0] next_pc;         // 下一条PC值
	wire [31:0] pc_plus_4;       // PC+4
	wire [31:0] inst_from_mem;   // 从指令存储器读出的指令
	wire [31:0] current_inst;    // 当前指令寄存器的值
	wire [4:0]  gpr_dest_addr;   // GPR目标寄存器地址 (Mux1输出)
	wire [31:0] gpr_write_data;  // 最终写入GPR的数据 (Mux2输出)
	wire [31:0] gpr_read_data_a; // GPR读端口A数据 (busa)
	wire [31:0] gpr_read_data_b; // GPR读端口B数据 (busb)
	wire [31:0] imm_extended;    // 32位符号扩展后的立即数
	wire [31:0] alu_operand_a_reg; // 锁存的ALU操作数A
	wire [31:0] alu_operand_b_reg; // 锁存的ALU操作数B
	wire [31:0] alu_operand_b;   // 送入ALU的操作数B (Mux3输出)
	wire [31:0] alu_result;      // ALU运算结果 (寄存器前)
	wire [31:0] alu_result_reg;  // 锁存的ALU运算结果
	wire [31:0] mem_read_data;   // 从数据存储器读出的数据
	wire [31:0] mem_read_data_reg; // 锁存的访存数据
	wire [31:0] data_from_mem_or_bridge; // Mux4输出
	wire [31:0] cp0_read_data;   // 从CP0读出的数据
	wire [31:0] exception_pc;    // 异常PC

	// --- ALU状态标志 ---
	wire zero;                  // ALU零标志
	wire overflow;              // ALU溢出标志

	// --- Bridge及外设相关信号 ---
	wire [31:0] bridge_read_data;      // 从Bridge读出的外设数据
	wire [31:0] timer_read_data;       // 从Timer读出的数据
	wire [31:0] output_dev_read_data;  // 从输出设备读出的数据
	wire [31:0] device_write_data;     // 写入外设的数据
	wire [31:0] device_addr;           // 外设地址
	wire bridge_we;             // Bridge写使能
	wire timer_irq;             // Timer中断请求
	wire timer_we;              // Timer写使能
	wire output_dev_we;         // 输出设备写使能
	wire [5:0] hardware_int_vector; // 硬件中断向量

	// 模块实例化
	PC PC(clk, pc_we, next_pc, pc_current);
	NPC NPC(pc_current, gpr_read_data_a, next_pc_op, zero, current_inst[25:0], next_pc, pc_plus_4, rst, exception_pc, clear_exl, jump_to_int_vector);
	ALU ALU(alu_operand_a_reg, alu_operand_b, alu_op, zero, overflow, alu_result);
	ALUOUT ALU_Out(clk, alu_result, alu_result_reg);
	AR AR(clk, gpr_read_data_a, alu_operand_a_reg);
	BR BR(clk, gpr_read_data_b, alu_operand_b_reg);	
	EXT EXT(current_inst[15:0], ext_op, imm_extended);	
	IM IM(pc_current[12:0], inst_from_mem);
	IR IR(ir_we, inst_from_mem, current_inst, clk);
	GPR GPR(clk, rst, gpr_we, gpr_dest_addr, gpr_write_data, current_inst[25:21], current_inst[20:16], gpr_read_data_a, gpr_read_data_b);
	DM DM(alu_result_reg[13:0], alu_operand_b_reg, mem_we, clk, is_lb, is_sb, mem_read_data);
	DR DR(clk, mem_read_data, mem_read_data_reg);		
	
	// 目标寄存器地址选择器
	mux_1 u_m1(gpr_dest_sel, current_inst[20:16], current_inst[15:11], gpr_dest_addr);
	
	// GPR写回数据选择器
	mux_2 u_m2(gpr_wr_data_sel, alu_result_reg, data_from_mem_or_bridge, pc_plus_4, gpr_write_data, cp0_read_data);
	
	// ALU操作数B选择器
	mux_3 u_m3(bsel, alu_operand_b_reg, imm_extended, alu_operand_b);
	
	// 访存/外设数据源选择器
	mux_4 u_m4(mem_read_data_reg, bridge_read_data, data_from_mem_or_bridge, alu_result_reg);
	controller Controller(clk, current_inst[31:26], current_inst[5:0], alu_op, gpr_dest_sel, gpr_we, ext_op, mem_we,
								gpr_wr_data_sel, next_pc_op, bsel, overflow, rst, pc_we, ir_we, zero, is_lb, is_sb,
								current_inst[25:21], internal_int_req, cp0_we, bridge_we, set_exl, clear_exl, jump_to_int_vector);	
	outputDEV OutputDevice(clk, output_dev_we, device_addr[3:2], device_write_data, output_dev_read_data, Data2out);
	Timer Timer(clk, rst, device_addr[3:2], timer_we, device_write_data, timer_read_data, timer_irq, cnt);
	CP0 CP0(pc_current, gpr_read_data_b, hardware_int_vector, current_inst[15:11], cp0_we, set_exl, clear_exl, clk, rst, internal_int_req, exception_pc, cp0_read_data);
	Bridge Bridge (alu_result_reg, gpr_read_data_b, bridge_read_data, timer_read_data, dev1_rd, output_dev_read_data, 
						device_write_data, device_addr, bridge_we, timer_we, output_dev_we, hardware_int_vector, timer_irq);

	// 将内部中断请求连接到顶层输出端口
	assign IntReq = internal_int_req;

endmodule