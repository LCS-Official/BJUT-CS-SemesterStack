module Re(
    input [31:0] d,
    input wr_enable,
	 input w_r,
    input reset,
    input clk,
    output reg [31:0] q
);

    always @(posedge clk or posedge reset) begin
        if (reset)
            q <= 32'b0;
        else if (!w_r&&wr_enable)
            q <= d;
    end

endmodule
