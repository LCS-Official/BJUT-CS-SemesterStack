module controller(op, func, aluop, gprsel, gprwr, extop, dmwr,
                   wdsel, npcop, bsel, overflow,
                   clk,rst,pcwr,irwr,lb_flag,sb_flag,zero,
                   IntReq,EXLSet,EXLClr,cp0_wen,bridge_wen,IntPc,MF,chan);
    input [5:0] op, func;
    input overflow;//adddi指令在有无溢出情况下 不同控制信号

    output gprwr;
    output dmwr; 
    output bsel;//0 busb 1 imm拓展后
    output [1:0] gprsel;//00 rt 01 rd 10 31 11 30
    output [1:0] extop;//00 01 10
    output [2:0] wdsel;//00 aluout 01 dmout 10 pc+4
    output [1:0] npcop;//00 pc4 01 beq 10 j/jal 11 jr
    output [2:0] aluop;//000 加 001 减 010或 011小于 100addi加

    input clk,rst,zero;
    
    output pcwr,irwr,lb_flag,sb_flag;

    input IntReq;
    input [4:0] MF;

    output EXLSet,EXLClr,cp0_wen,bridge_wen,IntPc;

    output chan;


    //表达所有指令
    //计算
    wire addu = (op == 6'b0) && (func == 6'b100001);
    wire subu = (op == 6'b0) && (func == 6'b100011);
    wire ori = (op == 6'b001101);
    wire addi = (op == 6'b001000);
    wire addiu = (op == 6'b001001);
    wire slt = (op == 6'b0) && (func == 6'b101010);
    wire lui = (op == 6'b001111);
    //跳转
    wire j = (op == 6'b000010); 
    wire jal = (op == 6'b000011);
    wire jr = (op == 6'b0) && (func == 6'b001000);
    //分支
    wire beq = (op == 6'b000100);
    //读mem
    wire lw = (op == 6'b100011);
    wire lb = (op == 6'b100000);
    //写mem
    wire sw = (op == 6'b101011);
    wire sb = (op == 6'b101000);

    wire eret = (op == 6'b010000) && (func == 6'b011000);
    wire mtc0 = (op == 6'b010000) && (MF == 5'b00100);
    wire mfc0 = (op == 6'b010000) && (MF == 5'b00000);


    //状态寄存器
    reg [3:0] cur_state, next_state;


    //定义状态编号
    parameter [3:0] S0 = 4'b0000;
    parameter [3:0] S1 = 4'b0001;
    parameter [3:0] S2 = 4'b0010;
    parameter [3:0] S3 = 4'b0011;
    parameter [3:0] S4 = 4'b0100;
    parameter [3:0] S5 = 4'b0101;
    parameter [3:0] S6 = 4'b0110;
    parameter [3:0] S7 = 4'b0111;
    parameter [3:0] S8 = 4'b1000;
    parameter [3:0] S9 = 4'b1001;
    parameter [3:0] S10 = 4'b1010;

    
    //状态转移 每到一个时钟沿 变成下一状态
    always@(posedge clk, posedge rst)
        if(rst)
            cur_state <= S0;
        else
            cur_state <= next_state;

  //根据信号 判断下一状态是什么
    always@(*)
        case(cur_state)
        S0: next_state = S1;//取指后译码 每个指令都是
        S1: begin
            if(lb | lw | sb | sw | mtc0 | mfc0) next_state = S2; //计算mem address 
            else if(addu | subu | ori | addi | addiu | lui | slt) next_state = S6;//执行计算
            else if(beq) next_state = S8;//分支 branch
            else if(j | jal | jr | eret) next_state = S9; //无条件跳转
            else  next_state = S0; 
        end
        S2: begin
            if(lw | lb | mfc0)  next_state = S3;  //MR mem read 从mem读
            else if(sw | sb | mtc0)  next_state = S5; //MW mem write 写入mem
            else  next_state = S0; 
        end
        S3: if(!IntReq) next_state = S4; else next_state = S10;
        S4: if(!IntReq) next_state = S0; else next_state = S10;
        S5: if(!IntReq) next_state = S0; else next_state = S10;
        S6: next_state = S7;
        S7: if(!IntReq) next_state = S0; else next_state = S10;
        S8: if(!IntReq) next_state = S0; else next_state = S10;
        S9: if(!IntReq) next_state = S0; else next_state = S10;
        S10:next_state = S0;
        default: next_state = S0;
        endcase
    
    //当前状态 用于看控制信号是什么
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

    //控制信号
    //000 add: addu
    //001 sub(beq) : subu beq
    //010 ori : ori
    //011 slt : slt
    //100 addi : addi
    assign aluop[2] = addi;
    assign aluop[1] = (ori | slt);
    assign aluop[0] = (subu | beq | slt);

    //gprsel
    //00:rt : i型 ori lui addi addiu
    //01:rd : r型指令：addu subu slt
    //10：31reg : jal存返回地址
    //11：30reg（overflow) : addi+overflow
    assign gprsel[1] = (jal | (overflow & addi));
    assign gprsel[0] = (addu | subu | slt | (overflow & addi));

    //extop
    //00 无符号
    //01 sign_ext : lw sw lb sb(address) addi 
    //11: lui
    assign extop[1] = lui;
    assign extop[0] = (lw | sw | lb | sb | addi );

    //bsel
    //0 b
    //1 imm: ori lw sw lui addi addiu lb sb
    assign bsel =  (ori | lw | sw | lui | addi | addiu | lb | sb) ;

    //wdsel
    //00:aluout
    //01:dmout : lw lb
    //10:pc+4 : jal
    //11:溢出位 : overflow+addi
    assign wdsel[2] = mfc0; //设备数据写入
    assign wdsel[1] = ((overflow & addi) | jal);
    assign wdsel[0] = ((lb | lw) | (overflow & addi));

    //sw sb 在状态5 MW 才能写入dm
    assign dmwr = ((sw | sb) & s5);

    //lb lw在s4 从dm读出的写入寄存器
    //jal 在s9 pc+4写回
    //addu subu ori addi addiu lui slt 在s7 执行完运算后 写回
    assign gprwr = ((lb | lw | mfc0) & s4) | ((jal) & s9) | ((addu | subu | ori | addi | addiu | lui | slt) & s7);
    
    //npcop 
    //00:pc+4
    //01 : beq
    //10 : j/jal
    //11 : jr
    assign npcop[1] = (j | jal | jr ) & (~s0);
    assign npcop[0] = (beq | jr ) & (~s0);

    //pc写使能
    //s0 取指阶段
    //beq+zero+s8 分支 新pc
    //jal j jr无条件跳转 新pc
    //s10pc+4存到epc 中断返回时调用
    //此时的pc写入中断执行程序的指定地址
    assign pcwr = (s0 | ((beq & zero) & s8) | (( jal | j | jr) & s9) | s10 | (eret & s9));

    //ir 只在取指阶段 变化
    assign irwr = s0;
    assign chan = s0;

    //lb和sb指令
    assign lb_flag = (lb==1)?1:0;
    assign sb_flag = (sb==1)?1:0;

    assign EXLSet = s10;//表示中断中 不可再中断
    assign EXLClr = eret;
    assign cp0_wen = mtc0 & s5; //从rt写到cp0
    assign bridge_wen = (sw | sb ) & s5;//数据存入外设
    assign IntPc = IntReq & s10;
  
endmodule