module controller(clk, OpCode, Funct, ALUOp, gprsel, gprwr, extop, dmwr,
                   wdsel, npcop, bsel, overflow, rst, pcwr, irwr, zero,islb,issb,
                   MF,IntReq, cp0_wen, bridge_wen, EXLSet, EXLClr, IntPc);
  input clk;
  input [5:0] OpCode, Funct;
  output [2:0] ALUOp, wdsel;
  output [1:0] gprsel;
  output gprwr;
  output [1:0] extop, npcop;
  output dmwr, bsel;
  input overflow;
  input rst;
  output pcwr, irwr;
  input zero;
  output islb, issb;
  input [4:0] MF;// 协处理器操作字段(5位)
  input IntReq;// 中断请求输入

  output cp0_wen, bridge_wen, EXLSet, EXLClr, IntPc;// CP0寄存器写使能,系统桥写使能,设置异常级别标志,清除异常级别标志,中断PC跳转标志
  
// 状态机状态定义
  parameter [3:0] S0 = 4'b0000;// 取指状态：从IM读取指令
  parameter [3:0] S1 = 4'b0001;// 译码状态：解析指令类型
  parameter [3:0] S2 = 4'b0010;// 访存准备状态：确定加载/存储类型
  parameter [3:0] S3 = 4'b0011;// 加载指令执行状态：从DM读数据
  parameter [3:0] S4 = 4'b0100;// 加载指令写回状态：数据写入寄存器
  parameter [3:0] S5 = 4'b0101;// 存储/协处理器写状态：数据写入DM或CP0
  parameter [3:0] S6 = 4'b0110;// 算术逻辑指令准备状态
  parameter [3:0] S7 = 4'b0111;// 算术逻辑指令写回状态
  parameter [3:0] S8 = 4'b1000;// 条件分支判断状态
  parameter [3:0] S9 = 4'b1001;// 跳转指令执行状态
  parameter [3:0] S10 = 4'b1010;// 中断处理状态：跳转至中断入口

  // 指令类型检测逻辑（组合逻辑）
  wire addu = (OpCode == 6'b0) && (Funct == 6'b100001);
  wire subu = (OpCode == 6'b0) && (Funct == 6'b100011);
  wire ori = (OpCode == 6'b001101);
  wire addi = (OpCode == 6'b001000);
  wire addiu = (OpCode == 6'b001001);
  wire slt = (OpCode == 6'b0) && (Funct == 6'b101010);
  wire lui = (OpCode == 6'b001111);
  wire j = (OpCode == 6'b000010); 
  wire jal = (OpCode == 6'b000011);
  wire beq = (OpCode == 6'b000100);
  wire jr = (OpCode == 6'b0) && (Funct == 6'b001000);
  wire lw = (OpCode == 6'b100011);
  wire lb = (OpCode == 6'b100000);
  wire sw = (OpCode == 6'b101011);
  wire sb = (OpCode == 6'b101000);
  
  wire eret = (OpCode == 6'b010000) && (Funct == 6'b011000);
  wire mtc0 = (OpCode == 6'b010000) && (MF == 5'b00100);
  wire mfc0 = (OpCode == 6'b010000) && (MF == 5'b00000);
  
  reg [3:0] cur_state, next_state;
  
  // 状态跳转逻辑
  always@(posedge clk, posedge rst)
    if(rst)
      cur_state <= S0;
    else
      cur_state <= next_state;
  
   // 根据当前状态和输入确定下一状态
  always@(*)
    case(cur_state)
      S0: next_state = S1;// 取指、译码
      S1: begin
        // 访存指令或协处理器指令
        if(lb | lw | sb | sw | mtc0 | mfc0) next_state = S2; 
		  // 算术逻辑指令
        else if(addu | subu | ori | addi | addiu | lui | slt) next_state = S6;
		  // 条件分支指令
        else if(beq) next_state = S8;
        // 跳转指令(含ERET)
        else if(j | jal | jr | eret) next_state = S9;
        else  next_state = S0;// 非法状态回到S0
      end
      S2: begin
        // 加载指令或读CP0
        if(lw | lb | mfc0)  next_state = S3;  
        // 存储指令或写CP0
        else if(sw | sb | mtc0)  next_state = S5;
        else  next_state = S0;
      end
     // 各状态中检测中断请求，若有则跳转至中断处理状态S10
      S3: if(!IntReq) next_state = S4; else next_state = S10;
      S4: if(!IntReq) next_state = S0; else next_state = S10;
      S5: if(!IntReq) next_state = S0; else next_state = S10;
      S6: next_state = S7;// 算术逻辑指令进入写回状态
      S7: if(!IntReq) next_state = S0; else next_state = S10;
      S8: if(!IntReq) next_state = S0; else next_state = S10;
      S9: if(!IntReq) next_state = S0; else next_state = S10;
      S10:next_state = S0;// 中断处理完成回到S0
      default: next_state = S0;
    endcase
   // 状态标志位（当前状态的一位热码表示） 
  wire s0 = (cur_state == 4'd0);
  wire s1 = (cur_state == 4'd1);
  wire s2 = (cur_state == 4'd2);
  wire s3 = (cur_state == 4'd3);
  wire s4 = (cur_state == 4'd4);
  wire s5 = (cur_state == 4'd5);
  wire s6 = (cur_state == 4'd6);
  wire s7 = (cur_state == 4'd7);
  wire s8 = (cur_state == 4'd8);
  wire s9 = (cur_state == 4'd9);
  wire s10 = (cur_state == 4'd10);
  
 // 控制信号生成逻辑（组合逻辑，无时间顺序）
  assign ALUOp[2] = addi;// addi操作时ALUOp[2]=1
  assign ALUOp[1] = (ori | slt);// ori或slt操作时ALUOp[1]=1
  assign ALUOp[0] = (subu | beq | slt);// subu、beq或slt操作时ALUOp[0]=1
  assign gprsel[1] = (jal | (overflow & addi));// jal或addi溢出时选择$31/$30
  assign gprsel[0] = (addu | subu | slt | (overflow & addi));// 算术操作或溢出时选择目标寄存器
  assign extop[1] = lui;// lui操作时扩展方式为高16位
  assign extop[0] = (lw | sw | lb | sb | addi | addiu);// 访存或立即数指令需要符号扩展
  assign bsel =  (ori | lw | sw | lui | addi | addiu | lb | sb) ;// B端选择立即数的指令
  assign wdsel[2] = mfc0;// 读CP0时写回数据来自CP0
  assign wdsel[1] = ((overflow & addi) | jal);// addi溢出或jal时选择特殊写回值
  assign wdsel[0] = ((lb | lw) | (overflow & addi));//加载指令或溢出时选择对应写回源
  // 控制信号生成逻辑（时序逻辑，需结合状态）
  assign dmwr = ((sw | sb) & s5);// 存储指令在S5状态写DM
 // 寄存器写使能：加载指令在S4、jal在S9、算术逻辑指令在S7时有效
  assign gprwr = ((lb | lw | mfc0) & s4) | (jal & s9) | ((addu | subu | ori | addi | addiu | lui | slt) & s7);
  // 下一条PC计算控制：跳转指令在非S0状态时有效
  assign npcop[1] = (j | jal | jr) & (~s0);
  assign npcop[0] = (beq | jr) & (~s0);
 // PC写使能：S0状态、分支成功、跳转指令、中断处理、ERET时有效
  assign pcwr = (s0 | ((beq & zero) & s8) | ((jal | j | jr) & s9) | s10 | (eret & s9));
  assign irwr = s0;// 取指状态写指令寄存器
  assign islb = lb;// 字节加载控制
  assign issb = sb;// 字节存储控制
  
  assign cp0_wen = mtc0 & s5;// 写CP0寄存器在S5状态有效
  assign bridge_wen = (sw | sb) & s5; // 系统桥写使能（存储指令在S5状态）
  assign EXLSet = s10;// 进入中断处理状态时设置异常级别
  assign EXLClr = eret;// ERET指令清除异常级别
  assign IntPc = IntReq & s10;// 中断处理状态时触发PC跳转至中断入口

endmodule
