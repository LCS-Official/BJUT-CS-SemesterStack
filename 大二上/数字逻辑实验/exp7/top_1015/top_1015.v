module top_1015(
    input n_en,               // 电源使能信号
    input clk_50mhz,          // 50MHz时钟信号
    input coin_1,             // 1角硬币投币口
    input coin_5,             // 5角硬币投币口
    input coin_10,            // 10角硬币投币口
    input bill_10,            // 1元纸币投币口
    input bill_50,            // 5元纸币投币口
    input confirm,            // 确认投币按钮
    output reg [6:0] LED_out_high,  // 高位7段显示
    output reg [6:0] LED_out_low,   // 低位7段显示
    output [7:0] total        // 总金额（以角为单位）
);
    
    // 定义时钟信号
    reg clk_hjq;  // 用于给 vending_machine_1015 的时钟信号

    // 实例化 vending_machine_1015 模块
    vending_machine_1015 vending_machine (
        .clk_hjq(clk_hjq),       // 将时钟信号传递给 vending_machine_1015 模块
        .coin_1(coin_1),         // 传递投币口信号
        .coin_5(coin_5),
        .coin_10(coin_10),
        .bill_10(bill_10),
        .bill_50(bill_50),
        .confirm(confirm),
        .total(total)            // 输出总金额信号
    );
    
    // 实例化 BCD_7seg_1015 模块
    // 高位显示（将total的高4位传递给BCD显示模块）
    BCD_7seg_1015 BCD_high (
        .n_en(n_en),               // 电源使能信号
        .LED_in(total[7:4]),       // 传递总金额的高4位
        .LED_out(LED_out_high),    // 连接到高位的7段显示输出
        .sel()                     // 不需要使用选择信号
    );
    
    // 低位显示（将total的低4位传递给BCD显示模块）
    BCD_7seg_1015 BCD_low (
        .n_en(n_en),               // 电源使能信号
        .LED_in(total[3:0]),       // 传递总金额的低4位
        .LED_out(LED_out_low),     // 连接到低位的7段显示输出
        .sel()                     // 不需要使用选择信号
    );

endmodule
