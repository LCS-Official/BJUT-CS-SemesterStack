module seqdetector(clk, x, reset, z, c_state, n_state);

    input clk, x, reset;  // 时钟信号、输入检测位、复位信号
    output reg z;         // 输出信号，表示检测成功
    output reg [3:0] c_state, n_state;  // 当前状态和下一状态

    // 状态定义
    parameter S0 = 0, S1 = 1, S2 = 2, S3 = 3, S4 = 4, S5 = 5, S6 = 6, S7 = 7, S8 = 8;

    reg [7:0] bcd_sequence;  // 目标检测序列（8421 BCD）

    // 初始化目标检测序列为 40 的 BCD 表示
    always @(posedge clk) begin
        if (!reset) begin
            bcd_sequence <= 8'b01000000;  // 40 的 BCD 表示
        end
    end

    // 状态转移逻辑：逐位检测 BCD 序列
    always @(c_state, x) begin
        case (c_state)
            S0: if (x == bcd_sequence[7]) n_state <= S1; else n_state <= S0; // 检测最高位（第7位）
            S1: if (x == bcd_sequence[6]) n_state <= S2; else n_state <= S0; 
            S2: if (x == bcd_sequence[5]) n_state <= S3; else n_state <= S0; 
            S3: if (x == bcd_sequence[4]) n_state <= S4; else n_state <= S0; 
            S4: if (x == bcd_sequence[3]) n_state <= S5; else n_state <= S0; 
            S5: if (x == bcd_sequence[2]) n_state <= S6; else n_state <= S0; 
            S6: if (x == bcd_sequence[1]) n_state <= S7; else n_state <= S0; 
            S7: if (x == bcd_sequence[0]) n_state <= S8; else n_state <= S0; // 检测最低位（第0位）
            S8: n_state <= S0;  // 检测完成，回到初始状态
            default: n_state <= S0;
        endcase
    end

    // 输出逻辑：当状态到达 S8 时，表示检测完成
    always @(posedge clk) begin
        if (c_state == S8)
            z <= 1'b1;  // 完整检测到序列，z = 1
        else
            z <= 1'b0;  // 未检测完成，z = 0
    end

    // 状态更新逻辑
    always @(posedge clk) begin
        if (!reset)
            c_state <= S0;  // 初始化到 S0 状态
        else
            c_state <= n_state;  // 状态更新
    end

endmodule
