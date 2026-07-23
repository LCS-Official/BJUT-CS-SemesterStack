module De(
    input [2:0] addr,
    output reg d0,
    output reg d1,
    output reg d2,
    output reg d3,
    output reg d4,
    output reg d5,
    output reg d6,
    output reg d7
);

    always @(*) begin
        d0 = 1'b0;
        d1 = 1'b0;
        d2 = 1'b0;
        d3 = 1'b0;
        d4 = 1'b0;
        d5 = 1'b0;
        d6 = 1'b0;
        d7 = 1'b0;
        case (addr)
            3'b000: d0 = 1'b1;
            3'b001: d1 = 1'b1;
            3'b010: d2 = 1'b1;
            3'b011: d3 = 1'b1;
            3'b100: d4 = 1'b1;
            3'b101: d5 = 1'b1;
            3'b110: d6 = 1'b1;
            3'b111: d7 = 1'b1;
        endcase
    end

endmodule
