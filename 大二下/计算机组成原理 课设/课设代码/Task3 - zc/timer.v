module timer(CLK_I, RST_I, ADD_I, WE_I, DAT_I, DAT_O, IRQ, change); 
     
    input CLK_I;//时钟
    input RST_I;//复位
    input [5:2] ADD_I;  //地址输入 2位 0000-0011  0100-0111  1000-1011
    input WE_I;//写使能
    input [31:0] DAT_I; //32 位数据输入
    output [31:0] DAT_O;  //32 位数据输出
    output IRQ;  //中断请求

    input change;
    

    //TC中的三个寄存器 每个寄存器都为 32 位，共计占用 12B 空间
    reg [31:0] CTRL;//控制寄存器 决定该计数起停控制
    reg [31:0] PRESET; //初值寄存器 提供初始值
    reg [31:0] COUNT; //计数值寄存器

    initial begin
        CTRL = 0; 
        PRESET = 0; 
        COUNT = 0;
    end
    
    //CTRL 控制寄存器
    wire im;// 中断屏蔽 0 禁止 1 允许
    wire [1:0] mode;// 模式选择 00：0 01:1
    wire enable;// 计数器使能 0：停止计数 1：允许计数

    assign {im,mode,enable} = {CTRL[3],CTRL[2:1],CTRL[0]};
    /*
        当计数器倒计数为 0 后，计数器停止计数。
        当初值寄存器再次被外部写入后，初值寄存器值再次被加载至计数器，计数器重新启动倒计数。
        模式 0 通常用于产生定时中断。例如，为操作系统的时间片调度机制提供定时。
    */


    //发送中断请求：计数到0 中断没有屏蔽 模式是0
    assign IRQ = ((COUNT == 32'b0) & im & (mode == 2'b00)) ? 1 : 0;
   
    always@(posedge CLK_I)  begin
        //复位 三个寄存器都是0
        if(RST_I) begin CTRL = 0; PRESET = 0; COUNT = 0; end
        else if(WE_I)
            case(ADD_I)//选择数据写入哪个寄存器
                4'b0000:  CTRL <= DAT_I;
                4'b0001:  begin PRESET <= DAT_I; COUNT <= DAT_I;  end
                4'b0010:  COUNT <= DAT_I;
                default: $display("Illegal reg");
            endcase
        else if(enable && change) begin //计数使能 后允许计数
            if(COUNT > 0)
                COUNT <= COUNT - 1;
            else if(COUNT == 0)
                case(mode)
                2'b00:
                    //$display("Stop counting");
                    COUNT <= COUNT;
                2'b01:
                    COUNT <= PRESET;//循环
                default:
                    $display("Illegal mode");
                endcase
        end
    end
    
endmodule