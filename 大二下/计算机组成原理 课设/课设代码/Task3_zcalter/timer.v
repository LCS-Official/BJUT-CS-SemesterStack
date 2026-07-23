// =======================================================
//  timer 模块
// =======================================================
module timer(
    input           clk,
    input           rst,
    input  [3:0]    addr,
    input           Wr_en,
    input  [31:0]   data_in,
    output          pause_q,
    input           alt_sign,
    output [31:0]   data_out
);

    reg [31:0] ctrl_sign;
    reg [31:0] begin_reg;
    reg [31:0] cnt_reg;

    wire       pause_acc;
    wire [1:0] mode_sel;
    wire       enable;

    assign {pause_acc, mode_sel, enable} = {ctrl_sign[3], ctrl_sign[2:1], ctrl_sign[0]};
    assign pause_q = (cnt_reg == 32'h0) && pause_acc && (mode_sel == 2'b00);
    assign data_out = (addr == 4'h0) ? ctrl_sign :
                      (addr == 4'h1) ? begin_reg :
                      (addr == 4'h2) ? cnt_reg   :
                                       32'b0;

    always @(posedge clk) begin
        if (rst) begin
            ctrl_sign <= 32'h0;
            begin_reg <= 32'h0;
            cnt_reg   <= 32'h0;
        end
        else if (Wr_en) begin
            case (addr)
                4'h0: ctrl_sign <= data_in;
                4'h1: begin
                    begin_reg <= data_in;
                    cnt_reg   <= data_in;
                end
                4'h2: cnt_reg   <= data_in;
                default: ;
            endcase
        end
        else if (enable && alt_sign) begin
            if (cnt_reg > 0) begin
                cnt_reg <= cnt_reg - 1;
            end
            else begin 
                case (mode_sel)
                    2'b00: cnt_reg <= cnt_reg; // 模式0，计数到0后保持不变
                    2'b01: cnt_reg <= begin_reg; // 模式1，自动重载
                    default: ;
                endcase
            end
        end
    end

endmodule