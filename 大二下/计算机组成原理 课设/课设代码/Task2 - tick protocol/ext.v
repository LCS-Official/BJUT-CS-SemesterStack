// ext.v
module ext(
    input [15:0] imm,
    input sign_ext, // 1 for sign-extend, 0 for zero-extend
    output [31:0] ext_imm
);

    assign ext_imm = sign_ext ? {{16{imm[15]}}, imm} : {16'h0000, imm};

endmodule