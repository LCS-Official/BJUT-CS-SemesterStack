/*
 * --------------------------------------------------------------------
 * 模块名称: pc (Program Counter)
 * 描述:     一个带有写使能和异步复位的32位程序计数器。
 * --------------------------------------------------------------------
 */
module pc(
    input clk, rst,
    input PCWrite,
    input [31:0] NPC,
    output reg [31:0] PC
);
    always @(posedge clk or posedge rst) begin
        if (rst) PC <= 32'h0000_3000;
        else if (PCWrite) PC <= NPC;
    end
endmodule