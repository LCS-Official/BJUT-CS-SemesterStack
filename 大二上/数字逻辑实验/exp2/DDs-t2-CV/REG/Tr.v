module Tr(
    input [31:0] in,
    input enable,
    output [31:0] out
);

    assign out = enable ? in : 32'bz;

endmodule
