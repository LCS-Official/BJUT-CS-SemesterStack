`timescale 1ns / 1ps

module ov7670_sccb_init #(
    parameter integer CLK_FREQ_HZ  = 100_000_000,
    parameter integer SCCB_FREQ_HZ = 100_000
)(
    input  wire       clk,
    input  wire       rst_n,

    // OV7670 控制与 SCCB 引脚
    output wire       ov_xclk,
    output reg        ov_reset_n,
    output wire       ov_pwdn,

    output wire       sccb_sio_c,
    inout  wire       sccb_sio_d,

    // 初始化状态
    output reg        init_busy,
    output reg        init_done,
    output reg        init_error,

    // SCCB 调试输出
    output wire       sccb_busy,
    output wire       sccb_done,
    output wire       sccb_rd_valid,
    output wire [7:0] sccb_rd_data,

    output reg  [7:0] dbg_index,
    output reg  [7:0] dbg_reg_addr,
    output reg  [7:0] dbg_reg_data,
    output reg  [3:0] dbg_state
);

    assign ov_pwdn = 1'b0;

    reg [1:0] xclk_div;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            xclk_div <= 2'd0;
        else
            xclk_div <= xclk_div + 1'b1;
    end

    assign ov_xclk = xclk_div[1];

    localparam integer WAIT_5MS = CLK_FREQ_HZ / 200;
    localparam integer WAIT_2MS = CLK_FREQ_HZ / 500;

    reg [31:0] wait_cnt;

    reg  [7:0] rom_index;
    wire [7:0] rom_reg_addr;
    wire [7:0] rom_reg_data;
    wire       rom_valid;
    wire       rom_last;

    ov7670_reg_rom_rgb565 u_reg_rom (
        .index    (rom_index),
        .reg_addr (rom_reg_addr),
        .reg_data (rom_reg_data),
        .valid    (rom_valid),
        .last     (rom_last)
    );

    reg [7:0] cur_reg_addr;
    reg [7:0] cur_reg_data;
    reg       cur_last;

    reg        sccb_start;
    reg        sccb_rw;
    reg [7:0]  sccb_reg_addr;
    reg [7:0]  sccb_wr_data;
    wire       sccb_error;

    sccb_master #(
        .CLK_FREQ_HZ  (CLK_FREQ_HZ),
        .SCCB_FREQ_HZ (SCCB_FREQ_HZ)
    ) u_sccb_master (
        .clk      (clk),
        .rst_n    (rst_n),

        .start    (sccb_start),
        .rw       (sccb_rw),
        .reg_addr (sccb_reg_addr),
        .wr_data  (sccb_wr_data),

        .rd_data  (sccb_rd_data),
        .rd_valid (sccb_rd_valid),
        .busy     (sccb_busy),
        .done     (sccb_done),
        .error    (sccb_error),

        .sio_c    (sccb_sio_c),
        .sio_d    (sccb_sio_d)
    );

    localparam [3:0]
        S_RST_LOW        = 4'd0,
        S_WAIT_AFTER_RST = 4'd1,
        S_SW_RESET       = 4'd2,
        S_WAIT_SW_DONE   = 4'd3,
        S_WAIT_SW_DELAY  = 4'd4,
        S_LOAD_ROM       = 4'd5,
        S_WRITE_REG      = 4'd6,
        S_WAIT_WRITE     = 4'd7,
        S_NEXT_REG       = 4'd8,
        S_DONE           = 4'd9;

    reg [3:0] state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state         <= S_RST_LOW;
            dbg_state     <= S_RST_LOW;

            ov_reset_n    <= 1'b0;
            wait_cnt      <= 32'd0;

            sccb_start    <= 1'b0;
            sccb_rw       <= 1'b0;
            sccb_reg_addr <= 8'h00;
            sccb_wr_data  <= 8'h00;

            rom_index     <= 8'd0;

            cur_reg_addr  <= 8'h00;
            cur_reg_data  <= 8'h00;
            cur_last      <= 1'b0;

            init_busy     <= 1'b1;
            init_done     <= 1'b0;
            init_error    <= 1'b0;

            dbg_index     <= 8'd0;
            dbg_reg_addr  <= 8'h00;
            dbg_reg_data  <= 8'h00;
        end else begin
            sccb_start <= 1'b0;
            dbg_state  <= state;

            if (sccb_error)
                init_error <= 1'b1;

            case (state)

                S_RST_LOW: begin
                    ov_reset_n <= 1'b0;
                    init_busy  <= 1'b1;
                    init_done  <= 1'b0;

                    if (wait_cnt >= WAIT_5MS - 1) begin
                        wait_cnt   <= 32'd0;
                        ov_reset_n <= 1'b1;
                        state      <= S_WAIT_AFTER_RST;
                    end else begin
                        wait_cnt <= wait_cnt + 1'b1;
                    end
                end

                
                S_WAIT_AFTER_RST: begin
                    ov_reset_n <= 1'b1;

                    if (wait_cnt >= WAIT_5MS - 1) begin
                        wait_cnt <= 32'd0;
                        state    <= S_SW_RESET;
                    end else begin
                        wait_cnt <= wait_cnt + 1'b1;
                    end
                end

                S_SW_RESET: begin
                    if (!sccb_busy) begin
                        sccb_rw       <= 1'b0;
                        sccb_reg_addr <= 8'h12;
                        sccb_wr_data  <= 8'h80;
                        sccb_start    <= 1'b1;

                        dbg_reg_addr  <= 8'h12;
                        dbg_reg_data  <= 8'h80;

                        state         <= S_WAIT_SW_DONE;
                    end
                end

                S_WAIT_SW_DONE: begin
                    if (sccb_done) begin
                        wait_cnt <= 32'd0;
                        state    <= S_WAIT_SW_DELAY;
                    end
                end

                S_WAIT_SW_DELAY: begin
                    if (wait_cnt >= WAIT_2MS - 1) begin
                        wait_cnt  <= 32'd0;
                        rom_index <= 8'd0;
                        state     <= S_LOAD_ROM;
                    end else begin
                        wait_cnt <= wait_cnt + 1'b1;
                    end
                end

                S_LOAD_ROM: begin
                    dbg_index    <= rom_index;
                    dbg_reg_addr <= rom_reg_addr;
                    dbg_reg_data <= rom_reg_data;

                    if (!rom_valid) begin
                        state <= S_DONE;
                    end else begin
                        cur_reg_addr <= rom_reg_addr;
                        cur_reg_data <= rom_reg_data;
                        cur_last     <= rom_last;
                        state        <= S_WRITE_REG;
                    end
                end

                
                S_WRITE_REG: begin
                    if (!sccb_busy) begin
                        sccb_rw       <= 1'b0;
                        sccb_reg_addr <= cur_reg_addr;
                        sccb_wr_data  <= cur_reg_data;
                        sccb_start    <= 1'b1;
                        state         <= S_WAIT_WRITE;
                    end
                end

                
                S_WAIT_WRITE: begin
                    if (sccb_done) begin
                        if (cur_last) begin
                            state <= S_DONE;
                        end else begin
                            state <= S_NEXT_REG;
                        end
                    end
                end

               
                S_NEXT_REG: begin
                    rom_index <= rom_index + 1'b1;
                    state     <= S_LOAD_ROM;
                end

                S_DONE: begin
                    ov_reset_n <= 1'b1;
                    init_busy  <= 1'b0;
                    init_done  <= 1'b1;
                    state      <= S_DONE;
                end

                default: begin
                    state <= S_RST_LOW;
                end

            endcase
        end
    end

endmodule