// 内部异常，EXLSet=1，处理，从异常中返回
// 外部异常，HWInt 和多个条件，处理，返回
// 系统状态接口，读取和修改CPU的核心状态，mtc0/mfc0，GPR与CP0的数据交换，CPU和协处理器之间唯一桥梁

module CP0(PC, DIn, HWInt, Sel, Wr_en, EXLSet, EXLClr, clk, rst, IntReq, epc, DOut);
	input [31:0] PC;			// PC
	input [31:0] DIn;			// 写入数据
	input [5:0] HWInt;		// 中断请求信号
	input [4:0] Sel;			// 地址选择信号
	input Wr_en;					//	写使能信号
	input EXLSet, EXLClr;	// EXL = 1, EXL = 0
	input clk, rst;		
	output IntReq;				// 中断请求
	output [31:0] epc;		// EPC寄存器输出至NPC
	output [31:0] DOut; 		// CP0寄存器的输出数据
  
    // 定义常用CP0寄存器的地址常量
    parameter [4:0] Status = 5'd12; // 状态寄存器 (Status Register)
    parameter [4:0] CAUSE  = 5'd13; // 异常原因寄存器 (Cause Register)
    parameter [4:0] EPC    = 5'd14; // 异常程序计数器 (Exception Program Counter)
    parameter [4:0] PRID   = 5'd15; // 处理器ID寄存器 (Processor ID Register)
  
   // CP0 内部的32个32位寄存器文件
	reg [31:0] rf_cp0 [31:0];
	
   // --- 组合逻辑部分：从Status寄存器中提取关键状态位 ---
	wire [15:10] im = rf_cp0[Status][15:10];	// 中断屏蔽/允许位
	wire exl = rf_cp0[Status][1];					// 异常处理级别
	wire ie = rf_cp0[Status][0];					// 中断使能
	
   // --- 组合逻辑部分：输出逻辑 ---
   // 将EPC寄存器的当前值持续输出到epc端口
	assign epc = rf_cp0[EPC];	
	
   // 根据Sel地址选择信号，持续输出对应CP0寄存器的值到DOut端口 (!!!实现mfc0!!!)
	assign DOut = rf_cp0[Sel];	
    
    // 中断管理器（!!外设异常!!）：当满足所有条件时，才向CPU发出中断请求
    assign IntReq = |(HWInt & im) &   // 条件1: 存在一个硬件中断(HWInt)，且该中断未被屏蔽(im对应位为1)
                    ie &             // 条件2: 全局中断已使能(ie=1)
                    (~exl);          // 条件3: CPU当前未处于异常处理状态(exl=0)
						  // 现在忙吗？
  
    // --- 初始化逻辑 ---
    integer i;
    initial begin
        rf_cp0[Status][15:10] = 6'b000001; // 默认只允许最低位的硬件中断
        rf_cp0[Status][0] = 1'b1;         // 默认全局中断使能
        rf_cp0[CAUSE][15:10] = 6'b000001;  // Cause寄存器的中断部分与Status保持一致
        rf_cp0[PRID] = 32'h0000_0000;      // 处理器ID设为0
    end
  
   // --- 时序逻辑部分：寄存器状态的更新 ---
	always @(posedge clk)
		if (rst) 
			begin // 复位逻辑：将关键寄存器恢复到初始状态
				rf_cp0[Status][15:10] <= 6'b000001;
				rf_cp0[Status][0] <= 1'b1;
				rf_cp0[CAUSE][15:10] <= 6'b000001;
				rf_cp0[PRID] <= 32'h0000_0000;
			end
    else
        begin
            // 每个周期都更新Cause寄存器的[15:10]位，实时地、持续地记录当前有哪些硬件中断正在请求服务
            rf_cp0[CAUSE][15:10] <= HWInt;

            // (!!!实现 mtc0 指令!!!)，当写使能有效，且目标不是只读的Cause寄存器时，将DIn写入目标寄存器
            if (Wr_en && (Sel != CAUSE))
                rf_cp0[Sel] <= DIn;
            
            // （!!内部异常!!）当异常发生时 (EXLSet=1)，进入异常处理模式
            if (EXLSet)
                begin
                    // 1. 将Status寄存器的EXL位置1，表示进入异常状态，屏蔽新的中断
                    rf_cp0[Status][1] <= 1'b1;
                    // 2. 将导致异常的指令地址(PC)保存到EPC寄存器，以便未来返回
                    rf_cp0[EPC] <= PC;
                end
            // 当执行eret指令时 (EXLClr=1)，退出异常处理模式
            else if (EXLClr)
                // 将Status寄存器的EXL位清0，同时将IE位置1，从中断恢复
                rf_cp0[Status][1:0] <= 2'b01; 
        end
endmodule