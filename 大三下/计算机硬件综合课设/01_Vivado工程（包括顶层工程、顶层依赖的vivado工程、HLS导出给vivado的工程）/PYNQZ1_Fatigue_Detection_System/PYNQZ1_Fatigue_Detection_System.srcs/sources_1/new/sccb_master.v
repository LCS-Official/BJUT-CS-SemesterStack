`timescale 1ns / 1ps

module sccb_master #(
    parameter integer CLK_FREQ_HZ  = 100_000_000,
    parameter integer SCCB_FREQ_HZ = 100_000
)(
    input  wire       clk,
    input  wire       rst_n,

    input  wire       start,      
    input  wire       rw,         // 0: write, 1: read
    input  wire [7:0] reg_addr,
    input  wire [7:0] wr_data,

    output reg  [7:0] rd_data,
    output reg        rd_valid,   // 读完成后拉高 1 个 clk
    output reg        busy,
    output reg        done,       // 读/写完成后拉高 1 个 clk
    output reg        error,      // busy 时再次 start，拉高 1 个 clk

    output reg        sio_c,
    inout  wire       sio_d
);

    localparam [7:0] OV7670_WR_ID = 8'h42;
    localparam [7:0] OV7670_RD_ID = 8'h43;

    
    wire sda_in;
    reg  sda_reg;
    reg  sda_flag;

    IOBUF IOBUF_inst (
        .O  (sda_in),
        .IO (sio_d),
        .I  (sda_reg),
        .T  (~sda_flag)
    );

    
    localparam integer RAW_TICK_DIV = CLK_FREQ_HZ / (SCCB_FREQ_HZ * 4);
    localparam integer TICK_DIV     = (RAW_TICK_DIV < 1) ? 1 : RAW_TICK_DIV;

    function integer clog2;
        input integer value;
        integer i;
        begin
            value = value - 1;
            for (i = 0; value > 0; i = i + 1)
                value = value >> 1;
            clog2 = i;
        end
    endfunction

    localparam integer TICK_CNT_W = (TICK_DIV <= 1) ? 1 : clog2(TICK_DIV);

    reg [TICK_CNT_W-1:0] tick_cnt;
    reg                  tick;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tick_cnt <= {TICK_CNT_W{1'b0}};
            tick     <= 1'b0;
        end else begin
            if (tick_cnt == TICK_DIV - 1) begin
                tick_cnt <= {TICK_CNT_W{1'b0}};
                tick     <= 1'b1;
            end else begin
                tick_cnt <= tick_cnt + 1'b1;
                tick     <= 1'b0;
            end
        end
    end

    localparam [4:0]
        ST_IDLE       = 5'd0,

        ST_START_A    = 5'd1,
        ST_START_B    = 5'd2,
        ST_START_C    = 5'd3,

        ST_TX_SETUP   = 5'd4,
        ST_TX_HIGH1   = 5'd5,
        ST_TX_HIGH2   = 5'd6,
        ST_TX_LOW     = 5'd7,

        ST_DC_SETUP   = 5'd8,
        ST_DC_HIGH1   = 5'd9,
        ST_DC_HIGH2   = 5'd10,
        ST_DC_LOW     = 5'd11,

        ST_READ_SETUP = 5'd12,
        ST_READ_HIGH1 = 5'd13,
        ST_READ_HIGH2 = 5'd14,
        ST_READ_LOW   = 5'd15,

        ST_NA_SETUP   = 5'd16,
        ST_NA_HIGH1   = 5'd17,
        ST_NA_HIGH2   = 5'd18,
        ST_NA_LOW     = 5'd19,

        ST_STOP_A     = 5'd20,
        ST_STOP_B     = 5'd21,
        ST_STOP_C     = 5'd22,
        ST_STOP_D     = 5'd23;

    reg [4:0] state;

    reg       op_read;
    reg [7:0] reg_addr_l;
    reg [7:0] wr_data_l;

    reg [7:0] tx_shift;
    reg [7:0] rd_shift;
    reg [2:0] bit_cnt;

    reg [1:0] phase_idx;

    reg       read_part;        // 0: 写寄存器地址阶段；1: 读数据阶段
    reg       restart_pending;  // 读操作第一段 STOP 后重新 START

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state           <= ST_IDLE;

            sio_c           <= 1'b1;
            sda_reg         <= 1'b0;
            sda_flag        <= 1'b0;

            rd_data         <= 8'h00;
            rd_valid        <= 1'b0;
            busy            <= 1'b0;
            done            <= 1'b0;
            error           <= 1'b0;

            op_read         <= 1'b0;
            reg_addr_l      <= 8'h00;
            wr_data_l       <= 8'h00;

            tx_shift        <= 8'h00;
            rd_shift        <= 8'h00;
            bit_cnt         <= 3'd7;

            phase_idx       <= 2'd0;
            read_part       <= 1'b0;
            restart_pending <= 1'b0;
        end else begin
            done     <= 1'b0;
            rd_valid <= 1'b0;
            error    <= 1'b0;

            if (start && busy)
                error <= 1'b1;

            if (state == ST_IDLE) begin
                sio_c    <= 1'b1;
                sda_reg  <= 1'b0;
                sda_flag <= 1'b0;
                busy     <= 1'b0;

                if (start) begin
                    busy            <= 1'b1;
                    op_read         <= rw;
                    reg_addr_l      <= reg_addr;
                    wr_data_l       <= wr_data;

                    phase_idx       <= 2'd0;
                    read_part       <= 1'b0;
                    restart_pending <= 1'b0;

                    state           <= ST_START_A;
                end
            end

            else if (tick) begin
                case (state)

                    
                    ST_START_A: begin
                        sio_c    <= 1'b1;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b0;   // 释放 SDA，高
                        state    <= ST_START_B;
                    end

                    ST_START_B: begin
                        sio_c    <= 1'b1;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b1;   // 拉低 SDA，产生 START
                        state    <= ST_START_C;
                    end

                    ST_START_C: begin
                        sio_c    <= 1'b0;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b1;

                        bit_cnt  <= 3'd7;

                        if (!op_read)
                            tx_shift <= OV7670_WR_ID;
                        else if (!read_part)
                            tx_shift <= OV7670_WR_ID;
                        else
                            tx_shift <= OV7670_RD_ID;

                        state <= ST_TX_SETUP;
                    end

                    
                    ST_TX_SETUP: begin
                        sio_c <= 1'b0;

                        if (tx_shift[bit_cnt] == 1'b0) begin
                            // 发送 0：主动拉低 SDA
                            sda_reg  <= 1'b0;
                            sda_flag <= 1'b1;
                        end else begin
                            // 发送 1：释放 SDA
                            sda_reg  <= 1'b0;
                            sda_flag <= 1'b0;
                        end

                        state <= ST_TX_HIGH1;
                    end

                    ST_TX_HIGH1: begin
                        sio_c <= 1'b1;
                        state <= ST_TX_HIGH2;
                    end

                    ST_TX_HIGH2: begin
                        sio_c <= 1'b1;
                        state <= ST_TX_LOW;
                    end

                    ST_TX_LOW: begin
                        sio_c <= 1'b0;

                        if (bit_cnt == 3'd0) begin
                            state <= ST_DC_SETUP;
                        end else begin
                            bit_cnt <= bit_cnt - 1'b1;
                            state   <= ST_TX_SETUP;
                        end
                    end

                   
                    ST_DC_SETUP: begin
                        sio_c    <= 1'b0;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b0;   // 释放 SDA
                        state    <= ST_DC_HIGH1;
                    end

                    ST_DC_HIGH1: begin
                        sio_c <= 1'b1;
                        state <= ST_DC_HIGH2;
                    end

                    ST_DC_HIGH2: begin
                        sio_c <= 1'b1;
                        state <= ST_DC_LOW;
                    end

                    ST_DC_LOW: begin
                        sio_c <= 1'b0;

                        if (!op_read) begin
                            
                            if (phase_idx == 2'd0) begin
                                phase_idx <= 2'd1;
                                tx_shift  <= reg_addr_l;
                                bit_cnt   <= 3'd7;
                                state     <= ST_TX_SETUP;
                            end else if (phase_idx == 2'd1) begin
                                phase_idx <= 2'd2;
                                tx_shift  <= wr_data_l;
                                bit_cnt   <= 3'd7;
                                state     <= ST_TX_SETUP;
                            end else begin
                                restart_pending <= 1'b0;
                                state           <= ST_STOP_A;
                            end
                        end else if (!read_part) begin
                            
                            if (phase_idx == 2'd0) begin
                                phase_idx <= 2'd1;
                                tx_shift  <= reg_addr_l;
                                bit_cnt   <= 3'd7;
                                state     <= ST_TX_SETUP;
                            end else begin
                                restart_pending <= 1'b1;
                                state           <= ST_STOP_A;
                            end
                        end else begin
                            
                            rd_shift <= 8'h00;
                            bit_cnt  <= 3'd7;
                            state    <= ST_READ_SETUP;
                        end
                    end

                    
                    ST_READ_SETUP: begin
                        sio_c    <= 1'b0;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b0;   // 释放 SDA，让 OV7670 驱动
                        state    <= ST_READ_HIGH1;
                    end

                    ST_READ_HIGH1: begin
                        sio_c <= 1'b1;
                        state <= ST_READ_HIGH2;
                    end

                    ST_READ_HIGH2: begin
                        sio_c             <= 1'b1;
                        rd_shift[bit_cnt] <= sda_in;
                        state             <= ST_READ_LOW;
                    end

                    ST_READ_LOW: begin
                        sio_c <= 1'b0;

                        if (bit_cnt == 3'd0) begin
                            state <= ST_NA_SETUP;
                        end else begin
                            bit_cnt <= bit_cnt - 1'b1;
                            state   <= ST_READ_SETUP;
                        end
                    end

                    
                    ST_NA_SETUP: begin
                        sio_c    <= 1'b0;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b0;
                        state    <= ST_NA_HIGH1;
                    end

                    ST_NA_HIGH1: begin
                        sio_c <= 1'b1;
                        state <= ST_NA_HIGH2;
                    end

                    ST_NA_HIGH2: begin
                        sio_c <= 1'b1;
                        state <= ST_NA_LOW;
                    end

                    ST_NA_LOW: begin
                        sio_c   <= 1'b0;
                        rd_data <= rd_shift;
                        state   <= ST_STOP_A;
                    end

                    ST_STOP_A: begin
                        sio_c    <= 1'b0;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b1;   // SDA 先拉低
                        state    <= ST_STOP_B;
                    end

                    ST_STOP_B: begin
                        sio_c    <= 1'b1;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b1;   // SCL 高，SDA 仍低
                        state    <= ST_STOP_C;
                    end

                    ST_STOP_C: begin
                        sio_c    <= 1'b1;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b0;   // 释放 SDA，产生 STOP
                        state    <= ST_STOP_D;
                    end

                    ST_STOP_D: begin
                        sio_c    <= 1'b1;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b0;

                        if (restart_pending) begin
                            restart_pending <= 1'b0;
                            read_part       <= 1'b1;
                            phase_idx       <= 2'd0;
                            state           <= ST_START_A;
                        end else begin
                            busy     <= 1'b0;
                            done     <= 1'b1;
                            rd_valid <= op_read;
                            state    <= ST_IDLE;
                        end
                    end

                    default: begin
                        state    <= ST_IDLE;
                        sio_c    <= 1'b1;
                        sda_reg  <= 1'b0;
                        sda_flag <= 1'b0;
                        busy     <= 1'b0;
                    end

                endcase
            end
        end
    end

endmodule