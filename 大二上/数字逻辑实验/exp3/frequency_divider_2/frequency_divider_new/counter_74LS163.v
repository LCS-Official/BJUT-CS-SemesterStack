module counter_74LS163 (
    input wire clk,        // 时钟信号
    input wire clr_n,      // 清零信号，低电平有效
    input wire ld_n,       // 置数信号，低电平有效
    input wire enp,        // 使能输入信号
    input wire ent,        // 使能输出信号
    input wire [3:0] d,    // 数据输入，用于置数
    output reg [3:0] q,    // 4 位计数输出
    output wire rco        // 溢出信号
);

    // 溢出信号，当计数器为 1111 并且 ENT 为 1 时，RCO 输出为 1
    assign rco = (q == 4'b1111) && ent;

    always @(posedge clk or negedge clr_n) begin
        if (!clr_n) begin
            // CLR_N 为低电平时，清零计数器
            q <= 4'b0000;
        end else if (!ld_n) begin
            // LD_N 为低电平时，将输入 D 的值加载到 Q
            q <= d;
        end else if (enp && ent) begin
            // ENP 和 ENT 都为高时，进行加 1 计数
            q <= q + 1;
        end
        // 否则保持当前值
    end

endmodule
