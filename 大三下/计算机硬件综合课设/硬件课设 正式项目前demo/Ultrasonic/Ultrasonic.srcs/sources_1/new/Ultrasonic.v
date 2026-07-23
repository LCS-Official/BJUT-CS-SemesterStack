`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: LC_Co.Ltd
// Engineer: LC_State
// 
// Create Date: 03/16/2026 10:04:46 AM
// Design Name: Course Design Test Project
// Module Name: Ultrasonic
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
module Ultrasonic #(
    parameter integer INPUT_CLK_HZ = 100_000_000, //输入时钟频率默认为100MHz
    parameter integer T_TRIG_US = 10,             //触发脉冲宽度默认为10us
    parameter integer T_OVERTIME_US = 40000       //传感器反应超时时间默认为40ms
)
(
    input wire clk,
    input wire rstn,
    input wire en,
    input wire echo,
    output reg trig,
    output reg [21:0] distance, //测量结果，单位为um，最大距离为4m，位宽22位
    output reg dist_valid,      //输出测量结果有效标志位
    output reg error
);
    localparam IDLE=3'b000,
               TRIGGER=3'b001,
               WAIT_ECHO=3'b011,
               ECHO_RISING=3'b010,
               ECHO_HIGH=3'b110,
               ECHO_FALLING=3'b100,
               WAIT_NEXT=3'b101;

    reg clk_1M;
    reg [9:0]cnt_clk;           //输入时钟分频器，不超过1M
    reg [2:0]state;             //状态变量
    reg cnt_en;
    reg [16:0]cnt_meas;         //测量计时器，不超过81ms，位宽17位
    reg [16:0]echo_start;       //记录echo脉冲开始时间

    //分频器，输出1MHz时钟信号
    always @(posedge clk or negedge rstn) begin //异步复位，同步释放
        if(~rstn) begin
            clk_1M <= 1'b0;
            cnt_clk <= 10'd0;
        end
        else begin
            if(cnt_clk < INPUT_CLK_HZ/2_000_000)
                cnt_clk <= cnt_clk + 10'd1;
            else begin
                clk_1M <= ~clk_1M;
                cnt_clk <= 10'd0;
            end
        end
    end

    //测量计时
    always @(posedge clk_1M or negedge rstn) begin
        if(~rstn) begin
            cnt_meas <= 17'd0;
        end
        else begin
            if(cnt_en)
                cnt_meas <= cnt_meas + 17'd1;
            else
                cnt_meas <= 17'd0;
        end
    end

    //次态解码
    always @(posedge clk_1M or negedge rstn) begin
        if(~rstn)
            state <= IDLE;
        else begin
            case(state)
                IDLE:        state <= (en)?TRIGGER:state;
                TRIGGER:     state <= (cnt_meas>=T_TRIG_US)?WAIT_ECHO:state;
                WAIT_ECHO:   state <= (echo | (cnt_meas>T_OVERTIME_US))?ECHO_RISING: state;
                ECHO_RISING: state <= ECHO_HIGH;
                ECHO_HIGH:   state <= (~echo)?ECHO_FALLING:state;
                ECHO_FALLING:state <= WAIT_NEXT;
                WAIT_NEXT:   state <= (cnt_meas>T_OVERTIME_US)?IDLE:state;
            endcase
        end
    end

    //输出解码
    always @(*) begin
        if(~rstn) begin
            trig <= 1'b0;
            cnt_en <= 1'b0;
            distance <= 22'd0;
            dist_valid <= 1'b0;
            echo_start <= 17'd0;
            error <= 1'b0;
        end
        else begin
            case(state)
                IDLE:
                begin
                    trig <= 1'b0;
                    cnt_en <= 1'b0;
                    dist_valid <= 1'b0;
                    error <= 1'b0;
                end
                TRIGGER:
                begin
                    trig <= 1'b1;
                    cnt_en <= 1'b1;
                end
                WAIT_ECHO:
                begin
                    trig <= 1'b0;
                end
                ECHO_RISING:
                begin
                    echo_start <= cnt_meas;
                end
                ECHO_FALLING:
                begin
                    if((cnt_meas-echo_start)>=118 && (cnt_meas-echo_start)<=24000)
                    begin
                        distance <= (cnt_meas-echo_start)*170; //根据脉宽计算距离，单位为um
                        dist_valid <= 1'b1;
                    end
                    else
                        error <= 1'b1;
                end
            endcase
        end
    end
endmodule
