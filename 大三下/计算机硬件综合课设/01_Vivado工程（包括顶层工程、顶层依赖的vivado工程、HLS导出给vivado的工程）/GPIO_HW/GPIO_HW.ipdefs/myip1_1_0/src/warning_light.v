`timescale 1ns / 1ps

module warning_light (
    input  wire clk,
    input  wire rst_n,
    input  wire alert,       // 触发信号，上升沿有效
    output reg  led_r,
    output reg  led_g,
    output wire dbg_state,       // 1位
    output wire [15:0] dbg_cnt  // 低16位
);

    // ========== 红灯持续时间（仿真时请改为小值，例如 1000） ==========
    localparam RED_TIME = 300000000;   // 3秒 @100MHz 300——000——000
    // 仿真用：localparam RED_TIME = 1000;
assign dbg_state = state;
assign dbg_cnt   = cnt[15:0];
    // 29位计数器，最大值 > 300M
    reg [28:0] cnt;
    
    // 状态定义
    localparam IDLE = 1'b0;
    localparam RED  = 1'b1;
    reg state, next_state;

    // alert 上升沿检测
    reg alert_sync, alert_d1;
    wire alert_posedge;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            alert_sync <= 0;
            alert_d1   <= 0;
        end else begin
            alert_sync <= alert;
            alert_d1   <= alert_sync;
        end
    end
    assign alert_posedge = alert_sync && !alert_d1;

    // 状态机时序逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            cnt   <= 0;
            led_r <= 0;
            led_g <= 1;      // 初始绿灯亮
        end else begin
            state <= next_state;
            case (state)
                IDLE: begin
                    led_r <= 0;
                    led_g <= 1;
                    cnt   <= 0;
                end
                RED: begin
                    led_r <= 1;
                    led_g <= 0;
                    if (cnt < RED_TIME - 1) begin
                        cnt <= cnt + 1;
                    end else begin
                        cnt <= 0;   // 计时结束，归零
                    end
                end
                default: begin
                    led_r <= 0;
                    led_g <= 1;
                    cnt   <= 0;
                end
            endcase
        end
    end

    // 状态机组合逻辑
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (alert_posedge)
                    next_state = RED;
            end
            RED: begin
                if (cnt == RED_TIME - 1)
                    next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end

endmodule