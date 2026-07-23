`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/16/2026 10:10:18 AM
// Design Name: 
// Module Name: Ultrasonic_tb
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////
module Ultrasonic_tb();

    reg clk;
    reg rstn;
    reg en;
    reg echo;
    
    wire trig;
    wire [21:0] distance; //测量结果，单位为um，最大距离为4m，位宽22位
    wire dist_valid;      //输出测量结果有效标志位
    wire error;

    //初始化
    initial begin
        clk = 1'b0;
        rstn = 1'b0;
        en = 1'b0;
        echo = 1'b0;
        
        #100 rstn = 1'b1;
        #100 en = 1'b1;
        #100 echo = 1'b1;
        #8000 echo = 1'b0;
    end
    
    //生成时钟
    always #1 clk = ~clk;
    
    //例化待测电路
    Ultrasonic #(
        .INPUT_CLK_HZ(2_000_000),    //输入时钟频率修改为2MHz
        .T_TRIG_US(10),              //触发脉冲宽度默认为10us
        .T_OVERTIME_US(40000)        //传感器反应超时时间默认为40ms
    ) Ultrasonic_inst(
        .clk(clk),
        .rstn(rstn),
        .en(en),
        .echo(echo),
        .trig(trig),
        .distance(distance), //测量结果，单位为um，最大距离为4m，位宽22位
        .dist_valid(dist_valid),    //输出测量结果有效标志位
        .error(error)
    );
    
endmodule
