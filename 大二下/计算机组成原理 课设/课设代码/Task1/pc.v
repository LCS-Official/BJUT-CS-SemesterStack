/*
 * 模块名称: pc (Program Counter)
 * 文件名称: pc.v
 * 描述:     一个带有异步复位的32位程序计数器。
 */

module pc(
    input         clk,
    input         rst,
    input  [31:0] NPC,    // 输入: 来自NPC单元计算好的下一PC地址
    output reg [31:0] PC     // 输出: 当前PC地址
);

    // 核心逻辑: 使用标准的异步复位时序逻辑
    // --修正点--: 敏感列表增加了 posedge rst
    always @(posedge clk or posedge rst) begin
        // 复位逻辑的优先级最高
        if (rst) begin
            // 当复位信号有效时，PC强制回到指定的起始地址
            PC <= 32'h0000_3000;
        end else begin
            // 在每个时钟上升沿，将下一地址(NPC)更新为当前地址
            PC <= NPC;
        end
    end

endmodule