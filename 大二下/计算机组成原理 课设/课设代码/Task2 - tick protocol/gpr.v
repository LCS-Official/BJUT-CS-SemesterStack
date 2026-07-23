// gpr.v
`include "defines.v"
module gpr(
    input clk,
    input rst,
    input reg_write,
    input [4:0] read_reg1,
    input [4:0] read_reg2,
    input [4:0] write_reg,
    input [31:0] write_data,
    output [31:0] read_data1,
    output [31:0] read_data2
);

    reg [31:0] rf[31:0]; // 32个32位寄存器
    integer i;

    // 异步读
    assign read_data1 = (read_reg1 == 5'b0) ? 32'b0 : rf[read_reg1];
    assign read_data2 = (read_reg2 == 5'b0) ? 32'b0 : rf[read_reg2];

    // 同步写
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            // 可选的复位清零
            for (i=0; i<32; i=i+1) begin
                rf[i] <= 32'b0;
            end
        end else if (reg_write && (write_reg != 5'b0)) begin
            rf[write_reg] <= write_data;
            
            // 以下是根据文档建议的调试代码 
            // 在Modelsim中可以方便地观察寄存器变化
`ifdef DEBUG
            $display("--- REG WRITE --- PC: %h, ADDR: $%d, DATA: %h", U_MIPS.datapath.pc_reg.current_pc, write_reg, write_data);
            $display("R[00-07]=%8X, %8X, %8X, %8X, %8X, %8X, %8X, %8X", 0, rf[1], rf[2], rf[3], rf[4], rf[5], rf[6], rf[7]);
            $display("R[08-15]=%8X, %8X, %8X, %8X, %8X, %8X, %8X, %8X", rf[8], rf[9], rf[10], rf[11], rf[12], rf[13], rf[14], rf[15]);
            $display("R[16-23]=%8X, %8X, %8X, %8X, %8X, %8X, %8X, %8X", rf[16], rf[17], rf[18], rf[19], rf[20], rf[21], rf[22], rf[23]);
            $display("R[24-31]=%8X, %8X, %8X, %8X, %8X, %8X, %8X, %8X", rf[24], rf[25], rf[26], rf[27], rf[28], rf[29], rf[30], rf[31]);
`endif
        end
    end
endmodule