module pc (
    input           clk,
    input           rst,      // <-- 1. 添加 rst 输入端口
    input           pcwr,
    input  [31:0]   pcin,
    output reg [31:0] pcout
);

    // 使用 localparam 定义初始PC值，增加可读性和可维护性
    localparam INITIAL_PC = 32'h0000_3000;

    always @(posedge clk) begin
        if (rst) begin
            // 2. 当复位信号有效时，强制将PC设为初始值
            pcout <= INITIAL_PC;
        end
        else if (pcwr) begin
            // 3. 正常工作时，根据写使能更新PC
            pcout <= pcin;
        end
        // 当 rst=0 且 pcwr=0 时，pcout 的值应保持不变，符合寄存器特性。
    end

endmodule