// pc.v
module pc(
    input clk,
    input rst,
    input pc_write,
    input [31:0] next_pc,
    output reg [31:0] current_pc
);
    
    initial begin
        current_pc = 32'h0000_3000;
    end

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            current_pc <= 32'h0000_3000;
        end else if (pc_write) begin
            current_pc <= next_pc;
        end
    end

endmodule