// 文件名: Controller.v
// 总控单元
module Controller(rst, clk, op, func, reg_sel, alu_op, wd_sel, we, npc_sel, ext_op, regwrite, alu_sel, addien, slten, lben, sben, pcwr, irwr, zero);
// ---------- 模块端口定义 ----------
  input rst, clk, zero;
  input [5:0]op, func;
  output we, regwrite, addien, slten, alu_sel;
  output [1:0]reg_sel, wd_sel, npc_sel, ext_op;
  output [2:0]alu_op;
  output sben, lben;
  output reg pcwr, irwr;

// ---------- 内部信号和状态定义 ----------

  reg [3:0]fsm; // FSM状态寄存器
  
  wire fs0, fs1, fs2, fs3, fs4, fs5, fs6, fs7, fs8, fs9;
  // FSM状态定义
  parameter s0 = 0, s1 = 1, s2 = 2, s3 = 3, s4 = 4, s5 = 5, s6 = 6, s7 = 7, s8 = 8, s9 = 9;

// ---------- 指令译码逻辑 ----------
  wire addu = (op==6'b0 && func==6'b100001);
  wire subu = (op==6'b0 && func==6'b100011);
  wire ori = (op==6'b001101);
  wire lw = op==6'b100011;
  wire sw = op==6'b101011;
  wire beq = op==6'b000100;
  wire lui = op==6'b001111;
  wire j = op==6'b000010;
  wire addiu = op==6'b001001;
  wire jal = op==6'b000011;
  wire jr = (op==6'b0 && func==6'b001000);
  wire lb = (op==6'b100000);
  wire sb = (op==6'b101000);
  // new
  wire srav =(op==6'b000000 && func==6'b000111); 
  wire addi;
  wire slt;
  

  
  // 下面这几个只在非取指阶段有效
  assign addien = addi & !fs0;
  assign slten = slt & !fs0;
  assign sben = sb & !fs0;
  assign lben = lb & !fs0;

// ---------- FSM 状态转移逻辑 ----------
always @ (posedge clk or posedge rst) begin
	if (rst) begin // 如果 rst 信号高 有效
		fsm <= s0; 
	end
	else begin // 否则，在时钟上升沿正常工作
		case(fsm)
			s0:fsm <= s1; // 取指 -> 译码
			s1: // 译码阶段，根据指令类型决定下一状态
				if (sw|lw|sb|lb) fsm <= s2; // 访存指令 -> 计算地址
				else if (addu|subu|ori|lui|addi|addiu|slt|jr|srav) fsm <= s6; // ALU或jr指令 -> 执行
				else if (beq) fsm <= s8; // 分支指令 -> 分支完成
				else fsm <= s9; // 剩余的 j, jal 指令 -> 跳转完成
			s2: // 计算访存地址阶段
				if (lw|lb) fsm <= s3; // Load指令 -> 读内存
				else fsm <= s5; // Store指令 -> 写内存
			s3:fsm <= s4; // 读内存 -> 写回
			s4:fsm <= s0; // 写回 -> 取指
			s5:fsm <= s0; // 写内存 -> 取指
			s6:fsm <= s7; // 执行 -> ALU写回
			s7:fsm <= s0; // ALU写回 -> 取指
			s8:fsm <= s0; // 分支完成 -> 取指
			s9:fsm <= s0; // 跳转完成 -> 取指
		endcase
	end
end

// ---------- 控制信号生成逻辑 (组合逻辑) ----------
// -- PC和IR的写使能信号 --
always @ (*) begin
	pcwr = (fs0)|(beq&fs8&zero)|((jal|j)&fs9)|(jr&fs7); // PCWrite在以下情况有效
	irwr = (fs0);
end

// -- 将FSM状态解码成一系列“状态标志”wire --
  assign fs0 = fsm==s0;
  assign fs1 = fsm==s1;
  assign fs2 = fsm==s2;
  assign fs3 = fsm==s3;
  assign fs4 = fsm==s4;
  assign fs5 = fsm==s5;
  assign fs6 = fsm==s6;
  assign fs7 = fsm==s7;
  assign fs8 = fsm==s8;
  assign fs9 = fsm==s9;
  
// -- 其他控制信号的生成，后面的&确保在正确的时间、正确的指令条件下，特定信号为真 --
  // 当指令为sw或sb，且处于s5(写内存)状态时，写使能有效
  assign we = (sw|sb)&(fs5);
  // 在s4(访存写回)、s7(ALU写回)或s9(jal写回)时，寄存器写使能有效
		// new srav
  assign regwrite = (addu|subu|ori|lw|lb|lui|addi|addiu|slt|jal|srav) & (fs4|fs7|fs9);
  // addi指令的定义
  assign addi = op==6'b001000;
  assign slt = op==6'b0 && func==6'b101010;
  // ALU第二个操作数的来源：为1时选择立即数，为0时选择寄存器BusB
  assign alu_sel = (ori|lw|lb|sb|sw|lui|addi|addiu)&(!fs0);
  // 写回目标寄存器选择：0->rt, 1->rd, 2->$ra
		// new srav
  assign reg_sel = ((ori|lui|addi|addiu)&(fs1|fs6|fs7))|((lw|lb)&(fs1|fs2|fs3|fs4)) ? 0 : (addu|subu|slt|srav) & (fs1|fs6|fs7) ? 1 : (jal)&(fs9|fs1) ? 2 : 3;
  // ALU运算类型：0->add, 1->sub, 2->or
  assign alu_op = (addu|lw|lb|sb|sw|addi|addiu) & !fs0 ? 0 : // add
                (subu|beq|slt) & !fs0 ? 1 :                // sub
                (ori|lui) & !fs0 ? 2 :                     // or
                (srav) & !fs0 ? 3 :                        // srav
                0; // 默认操作
  // 写回寄存器的数据来源：0->ALU结果, 1->DM数据, 2->PC+4
  assign wd_sel = (addu|subu|ori|lui|addi|addiu|slt|srav) & (!fs0) ? 0 : (lw|lb)&(!fs0) ? 1 : (jal)&(!fs0) ? 2 : 3;
  // 下一个PC地址的来源：0->PC+4, 1->分支目标, 2->跳转目标, 3->寄存器(jr)
  assign npc_sel = (beq&fs8) ? 1 : (j|jal)&fs9 ? 2 : (jr&fs7) ? 3 : 0;
  // 立即数扩展方式：0->零扩展, 1->符号扩展, 2->LUI高16位扩展
  assign ext_op = (ori)&(!fs0) ? 0 : (lw|lb|sb|sw|addi|addiu)&(!fs0) ? 1 : (lui)&(!fs0) ? 2 : 3;

endmodule