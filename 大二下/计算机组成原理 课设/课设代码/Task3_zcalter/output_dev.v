module output_dev(
    input           clk,
    input           rst, 
    input           en,
    input  [3:0]    addr,
    input  [31:0]   din,
    output [31:0]   dout
);

    reg [31:0] preData, curData;


    always @(posedge clk) begin
        if (rst) begin
            // 当复位信号有效时，将内部寄存器强制清零
            preData <= 32'h0;
            curData <= 32'h0;
        end
        else if (en) begin
            // 正常工作时，根据地址选择性地写入数据
            case(addr)
                4'b1000: preData <= din;
                4'b1001: curData <= din;
                default: ; // 对于无效地址的写操作，不执行任何动作
            endcase
        end
    end

    // 读逻辑保持不变
	 // 只有当送给 output_dev 的内部地址 addr 是 8 或 9 时，dout才不是高阻态
    assign dout = (addr == 4'b1000) ? preData : (addr == 4'b1001) ? curData : 32'bz;

endmodule