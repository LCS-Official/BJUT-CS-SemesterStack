module frequency_divider_new (
    input clk_50mhz,      // 输入时钟
    input rst,            // 重置
    input [3:0] q_in,     // 计数器输入数据
    input clr_n,          // 清零
    input ld_n,           // 置数
    input enp,            
    input ent,            
    output rco,           // 计数器溢出信号
    output [3:0] q_out,   // 计数器输出
    output clk_1hz,       // 输出时钟
    output clk_10hz,     
    output clk_100hz,    
    output clk_1000hz     
);

    //frequency_divider individual
    frequency_divider frequency_divider_inst (
        .clk_50mhz(clk_50mhz),
        .rst(rst),
        .clk_1hz(clk_1hz),
        .clk_10hz(clk_10hz),
        .clk_100hz(clk_100hz),
        .clk_1000hz(clk_1000hz)
    );

    //74LS163 individual
    counter_74LS163 counter_74LS163_inst (
        .clk(clk_1hz),  
        .clr_n(clr_n),
        .ld_n(ld_n),
        .enp(enp),
        .ent(ent),
        .d(q_in),   
        .q(q_out),   
        .rco(rco)    
    );

endmodule
