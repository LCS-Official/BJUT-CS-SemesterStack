module cp0(pcout, rt_din, HWInt, Sel, cp0wr, EXLSet, EXLClr, clk, rst, IntReq, epc, cp0dout);
  input [31:0] pcout; //中断时 pc+4存入epc，中断返回
  input [31:0] rt_din; //从rt的输入，mtc0使用
  input [5:0] HWInt; //表示六个设备的中断信号，从bridge来
  input [4:0] Sel; //选择内部寄存器 mfc0 哪一个设备输出 mtc0 数据写入哪一个寄存器
  
  input cp0wr; //cp0写使能，遇到mtc0时允许通过
  input EXLSet, EXLClr;//exl的置位、清除
  input clk, rst;

  output IntReq;// 信号————是否中断
  output [31:0] epc;// 保存中断，异常时的PC+4 使得中断结束后程序返回
  output [31:0] cp0dout;  // pc0写给rt的 mfc0指令
  
 
  //4个寄存器
  parameter [4:0] SR = 5'd12; // 状态寄存器，用这个存储state状态，起到中断权限的控制
  parameter [4:0] CAUSE = 5'd13; // 中断原因寄存器
  parameter [4:0] EPC = 5'd14; // 异常程序计数器寄存器
  parameter [4:0] PRID = 5'd15; // 处理器ID寄存器
  
  reg [31:0] regarray_cp0 [31:0]; // 32个寄存器
  
  wire [15:10] im; // 设备允许中断
  wire exl, ie; // 是否在中断中 全局中断使能
  
  assign exl = regarray_cp0[SR][1]; // 进入中断后，必须标记，防止再次进入
  assign ie = regarray_cp0[SR][0]; // 全局中断使能 1 允许 
  assign im = regarray_cp0[SR][15:10]; // 6个设备哪个允许中断

  assign epc = regarray_cp0[EPC]; // 存中断发生时候的pc+4

  assign cp0dout = regarray_cp0[Sel];  // 选择输出某个设备的数据
  
  // 判断是否中断允许
  assign IntReq = | (HWInt & im) & ie & (~exl);
  
  integer i;
  
  initial begin
    for(i=0; i<32; i=i+1) regarray_cp0[i]=0;//初始化都为0

    regarray_cp0[SR][15:10] = 6'b000001;  //最低中断
    regarray_cp0[SR][0] = 1'b1;// 允许中断
    regarray_cp0[CAUSE][15:10] = 6'b000001;//中断原因
    regarray_cp0[PRID] = 32'h2307_0215;//备注
  end
  

  always@(posedge clk) begin
    //清零 恢复初始化
    if(rst) begin
      for(i=0; i<32; i=i+1) regarray_cp0[i]=0;
      //{im, exl, ie}<={6'b000001,1'b0,1'b1};
      regarray_cp0[SR][15:10] = 6'b000001;  // im
      regarray_cp0[SR][0] = 1'b1;           // ie
      regarray_cp0[CAUSE][15:10] = 6'b000001;
      regarray_cp0[PRID] = 32'h2307_0215;
    end
    
    if(cp0wr & (Sel != CAUSE))//写入cp0中某个寄存器
      regarray_cp0[Sel] <= rt_din;
    else if(EXLSet) begin // 如果exl置位信号是1 置位 进入中断 把pc+4存到epc
      regarray_cp0[SR][1] <= 1'b1;
      regarray_cp0[SR][0] <= 1'b0;
      regarray_cp0[EPC] <= pcout; 
    end
    else if(EXLClr) begin //如果中断返回 exl恢复0 选择epc作为npc输出
      regarray_cp0[SR][1] <= 1'b0;//当前不在中断
      regarray_cp0[SR][0] <= 1'b1;//系统允许中断
    end 
    else
      regarray_cp0[CAUSE] <= {16'b0, HWInt, 10'b0}; //接受来自桥的信号

    regarray_cp0[CAUSE] <= {16'b0, HWInt, 10'b0};
  end

endmodule