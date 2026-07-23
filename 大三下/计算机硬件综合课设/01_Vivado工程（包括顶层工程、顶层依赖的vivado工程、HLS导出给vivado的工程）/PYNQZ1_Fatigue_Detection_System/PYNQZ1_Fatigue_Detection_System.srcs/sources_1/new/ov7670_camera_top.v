`timescale 1ns / 1ps

module ov7670_camera_top #(
    parameter integer CLK_FREQ_HZ  = 100_000_000,
    parameter integer SCCB_FREQ_HZ = 100_000,

    parameter integer FRAME_WIDTH  = 640,
    parameter integer FRAME_HEIGHT = 480
)(
    input  wire        clk,
    input  wire        rst_n,

    input  wire        capture_enable,

    output wire        ov_xclk,
    output wire        ov_reset_n,
    output wire        ov_pwdn,
    output wire        sccb_sio_c,
    inout  wire        sccb_sio_d,

    input  wire        cam_pclk,
    input  wire        cam_vsync,
    input  wire        cam_href,
    input  wire [7:0]  cam_data,

    output wire [31:0] m_axis_tdata,
    output wire [3:0]  m_axis_tkeep,
    output wire        m_axis_tvalid,
    input  wire        m_axis_tready,
    output wire        m_axis_tlast,
    output wire        m_axis_tuser,

    output wire        axis_frame_active,
    output wire        axis_frame_done,
    output wire        axis_overflow,
    output wire [31:0] axis_sent_pixel_count,

    output wire        init_busy,
    output wire        init_done,
    output wire        init_error,

    output wire        sccb_busy,
    output wire        sccb_done,
    output wire        sccb_rd_valid,
    output wire [7:0]  sccb_rd_data,

    output wire [7:0]  dbg_sccb_index,
    output wire [7:0]  dbg_sccb_reg_addr,
    output wire [7:0]  dbg_sccb_reg_data,
    output wire [3:0]  dbg_sccb_state,

    output wire [15:0] pixel_data,
    output wire        pixel_valid,
    output wire [10:0] pixel_x,
    output wire [9:0]  pixel_y,

    output wire        frame_start,
    output wire        line_start,
    output wire        line_end,
    output wire        frame_valid,
    output wire        line_active,

    output wire [7:0]  dbg_byte_data,
    output wire        dbg_byte_valid,
    output wire        dbg_byte_phase
);

    ov7670_sccb_init #(
        .CLK_FREQ_HZ  (CLK_FREQ_HZ),
        .SCCB_FREQ_HZ (SCCB_FREQ_HZ)
    ) u_ov7670_sccb_init (
        .clk           (clk),
        .rst_n         (rst_n),

        .ov_xclk       (ov_xclk),
        .ov_reset_n    (ov_reset_n),
        .ov_pwdn       (ov_pwdn),

        .sccb_sio_c    (sccb_sio_c),
        .sccb_sio_d    (sccb_sio_d),

        .init_busy     (init_busy),
        .init_done     (init_done),
        .init_error    (init_error),

        .sccb_busy     (sccb_busy),
        .sccb_done     (sccb_done),
        .sccb_rd_valid (sccb_rd_valid),
        .sccb_rd_data  (sccb_rd_data),

        .dbg_index     (dbg_sccb_index),
        .dbg_reg_addr  (dbg_sccb_reg_addr),
        .dbg_reg_data  (dbg_sccb_reg_data),
        .dbg_state     (dbg_sccb_state)
    );

    reg init_done_pclk_d1;
    reg init_done_pclk_d2;

    always @(posedge cam_pclk or negedge rst_n) begin
        if (!rst_n) begin
            init_done_pclk_d1 <= 1'b0;
            init_done_pclk_d2 <= 1'b0;
        end else begin
            init_done_pclk_d1 <= init_done;
            init_done_pclk_d2 <= init_done_pclk_d1;
        end
    end

    wire dvp_rst_n;
    assign dvp_rst_n = rst_n & init_done_pclk_d2;

    ov7670_dvp #(
        .VSYNC_ACTIVE_LEVEL (1'b1),
        .HREF_ACTIVE_LEVEL  (1'b1),
        .SWAP_BYTES         (1'b0),
        .X_BITS             (11),
        .Y_BITS             (10)
    ) u_ov7670_dvp (
        .pclk           (cam_pclk),
        .rst_n          (dvp_rst_n),

        .cam_vsync      (cam_vsync),
        .cam_href       (cam_href),
        .cam_data       (cam_data),

        .pixel_data     (pixel_data),
        .pixel_valid    (pixel_valid),

        .pixel_x        (pixel_x),
        .pixel_y        (pixel_y),

        .frame_start    (frame_start),
        .line_start     (line_start),
        .line_end       (line_end),

        .frame_valid    (frame_valid),
        .line_active    (line_active),

        .dbg_byte_data  (dbg_byte_data),
        .dbg_byte_valid (dbg_byte_valid),
        .dbg_byte_phase (dbg_byte_phase)
    );

    to_vdma_axis #(
        .FRAME_WIDTH  (FRAME_WIDTH),
        .FRAME_HEIGHT (FRAME_HEIGHT),
        .X_BITS       (11),
        .Y_BITS       (10)
    ) u_dvp_to_vdma_rgb565 (
        .pclk                  (cam_pclk),
        .rst_n                 (dvp_rst_n),

        .capture_enable        (capture_enable),

        .frame_start           (frame_start),
        .pixel_data            (pixel_data),
        .pixel_valid           (pixel_valid),
        .pixel_x               (pixel_x),
        .pixel_y               (pixel_y),

        .m_axis_tdata          (m_axis_tdata),
        .m_axis_tkeep          (m_axis_tkeep),
        .m_axis_tvalid         (m_axis_tvalid),
        .m_axis_tready         (m_axis_tready),
        .m_axis_tlast          (m_axis_tlast),
        .m_axis_tuser          (m_axis_tuser),

        .axis_frame_active     (axis_frame_active),
        .axis_frame_done       (axis_frame_done),
        .axis_overflow         (axis_overflow),
        .axis_sent_pixel_count (axis_sent_pixel_count)
    );

endmodule