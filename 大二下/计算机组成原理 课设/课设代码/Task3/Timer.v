// 模式一提供“一次性”的精确延时，用中断打断 忙等待机
// 模式二提供“周期性”的系统节拍，每当倒计时到0，它就自动重置，为了简化不中断
// 提供稳定可靠的时钟源
module Timer(CLK_I, RST_I, ADD_I, WE_I, DAT_I, DAT_O, IRQ,COUNT);
	input CLK_I, RST_I, WE_I; 		// 时钟、复位信号、写使能
	input [3:2] ADD_I;    			// ADD_I: 来自CPU/Bridge的地址线，用于选择内部寄存器
	input [31:0] DAT_I;				// DAT_I: 来自CPU的数据总线，用于写入数据
	output [31:0] DAT_O;				// DAT_O: 读出的数据，送回给CPU
	output IRQ;							// IRQ: 中断请求线，倒计时完成时通知CPU
	output reg [31:0]COUNT;			// COUNT: 实时倒计数值，可被CPU读取
	
    // --- 内部信号和寄存器定义 ---
    wire im;                    // im: 中断屏蔽/使能位 (Interrupt Mask/Enable)
    wire [2:1] mode;            // mode: 工作模式选择位
    wire enable;                // enable: 计数使能位
    reg [31:0] CTRL, PRESET;    // CTRL: 控制寄存器; PRESET: 预置数/重载值寄存器
    reg [9:0] clk_counter;      // clk_counter: 10位时钟分频计数器
    
    // --- 从CTRL寄存器中解析出各个控制位 ---
    assign im = CTRL[3];        // 中断屏蔽位：0=禁止中断，1=允许中断
    assign mode = CTRL[2:1];    // 工作模式选择
	 // 0:从初值递减到0，然后停止；1:从初值递减到0，然后自动重载初值，继续计数
	 
    assign enable = CTRL[0];    // 计数使能位：0=停止计数，1=开始/继续计数

    // --- 读操作逻辑 (一个3选1的多路选择器) ---
    // 根据地址ADD_I，选择对应的寄存器值输出到DAT_O
    assign DAT_O = (ADD_I == 2'b00) ? CTRL :           // 地址00: 读控制寄存器
                   (ADD_I == 2'b01) ? PRESET :         // 地址01: 读预置计数值
                   (ADD_I == 2'b10) ? COUNT : 32'b0;    // 地址10: 读当前计数值

    // --- 中断请求生成逻辑 ---
    // 仅当满足所有以下条件时，才产生中断请求(IRQ=1)
    assign IRQ = ((COUNT == 32'b0) &   // 条件1: 倒计时已结束
                  im &                 // 条件2: 中断功能已允许
                  (mode == 2'b00)) ?   // 条件3: 当前工作在0模式 (!!!mode=00!!!)
                  1 : 0;
  
    // --- 初始化逻辑---
    initial begin
        CTRL = 0; PRESET = 0; COUNT = 0; clk_counter = 0;
    end
  
    // --- 主要的时序逻辑 ---
    always @ (posedge CLK_I) 
        if(RST_I) // 1. 复位逻辑
            begin 
                CTRL <= 0; 
                PRESET <= 0; 
                COUNT <= 0; 
                clk_counter <= 0;
            end
        else if(WE_I) // 2. CPU写操作逻辑，让闹钟更加灵活，属于配置闹钟的逻辑，用sw实现
            begin
                case(ADD_I)
                    2'b00: CTRL <= DAT_I;                               // 地址00: 写控制寄存器
                    2'b01: begin PRESET <= DAT_I; COUNT <= DAT_I; end   // 地址01: 写预置数，并立即用该值更新当前计数值
                    2'b10: COUNT <= DAT_I;                              // 地址10: 直接写当前计数值
                    default:;
                endcase
                clk_counter <= 0;  // 任何写操作后都重置分频器，确保时序同步
            end
        else if(enable) // 3. 倒计时逻辑 (仅当使能且无写操作时执行)
            begin
                // A. 时钟分频：每10个系统时钟周期，才产生一个“节拍”
                if(clk_counter == 9)
                    begin
                        clk_counter <= 0; // 分频器归零
                        // B. COUNT递减逻辑
                        if(COUNT > 0)
                            COUNT <= COUNT - 1; // 如果没到0，就减1
                        // C. 自动重载逻辑
                        else if(COUNT == 0 && mode == 2'b01) // 如果到0了，并且是自动重载模式
                            COUNT <= PRESET;                 // 就用PRESET的值重新加载COUNT
									 // 让倒计时永不停止，周而复始地进行
                    end
                else // 分频器累加
                    clk_counter <= clk_counter + 1;
            end
endmodule