module CP(
	input wire clk,
	input wire rst,
	input wire [31:0] PC,		// 保存 PC
	input wire [31:0] din,		// CP0 寄存器的写入数据
	input wire [5:0] hwint,		// 6个设备中断
	input wire [4:0] sel,		// 用于选择 CP0 内部的寄存器
	input wire wen,				// CPO 寄存器写使能
	input wire exlset,			// EXL = 1
	input wire exlclr,			// EXL = 0
	output wire intreg,			// 中断请求
	output wire [31:0] epc,		// EPC 寄存器输出至 NPC
	output wire [31:0] dout		// CP0 寄存器的输出数据
);
  
	// EPC 寄存器
	reg [31:2] EPC_reg;
	assign epc = {EPC_reg, 2'b0};
	// Cause 寄存器
	reg [5:0] hwint_pend;	
	// Status 寄存器
	reg [15:10] im;
	reg exl, ie;	
	
	initial begin
		EPC_reg <= 30'b0;
		hwint_pend <= 6'b000001;
		{im, exl, ie} <= {6'b000001, 1'b0, 1'b1};
	end
	
	// EPC 寄存器
	always @ (posedge clk, posedge rst)
		if(rst)
			EPC_reg <= 30'b0;
		else if(wen && sel == 5'b01110)
			EPC_reg <= din[31:2];
		else if(exlset)
			EPC_reg <= PC[31:2];

	// Cause 寄存器
	always @(posedge clk, posedge rst)
		if (rst)
			hwint_pend <= 6'b000001;
		else
			hwint_pend <= hwint;

	// Status 寄存器
	always @ (posedge clk, posedge rst)
		if(rst)
			{im, exl, ie} <= {6'b000001, 1'b0, 1'b1};
		else
			begin
				if(wen && sel == 5'b01100)
					{im, exl, ie} <= {din[15:10], din[1], din[0]};
				else if(exlset)
					exl <= 1;
				else if(exlclr) begin
					exl <= 0; ie <= 1;
				end
			end

	assign dout = 	(sel == 5'b01111) ? 32'h0000_0000:
						(sel == 5'b01110) ? {EPC_reg, 2'b0}:
						(sel == 5'b01101) ? {16'b0, hwint_pend, 10'b0}:
						(sel == 5'b01100) ? {16'b0, im, 8'b0, exl, ie}:
						32'b0;
	assign intreg = ie & ~exl & |(hwint_pend & im);						// 当 IE=1 且 EXL=0 且 有挂起中断与掩码 IM 匹配时拉高

endmodule