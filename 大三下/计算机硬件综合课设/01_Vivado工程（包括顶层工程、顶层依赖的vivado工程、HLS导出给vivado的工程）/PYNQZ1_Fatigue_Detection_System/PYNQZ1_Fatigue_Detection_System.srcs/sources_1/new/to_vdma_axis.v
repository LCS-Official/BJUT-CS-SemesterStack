`timescale 1ns / 1ps

module to_vdma_axis #(
    parameter integer FRAME_WIDTH  = 640,
    parameter integer FRAME_HEIGHT = 480,
    parameter integer X_BITS       = 11,
    parameter integer Y_BITS       = 10
)(
    input  wire                  pclk,
    input  wire                  rst_n,

    input  wire                  capture_enable,

    input  wire                  frame_start,
    input  wire [15:0]           pixel_data,
    input  wire                  pixel_valid,
    input  wire [X_BITS-1:0]     pixel_x,
    input  wire [Y_BITS-1:0]     pixel_y,

    output reg  [31:0]           m_axis_tdata,
    output wire [3:0]            m_axis_tkeep,
    output reg                   m_axis_tvalid,
    input  wire                  m_axis_tready,
    output reg                   m_axis_tlast,
    output reg                   m_axis_tuser,

    output reg                   axis_frame_active,
    output reg                   axis_frame_done,
    output reg                   axis_overflow,
    output reg  [31:0]           axis_sent_pixel_count
);

    assign m_axis_tkeep = 4'b1111;

    
    reg cap_en_d1;
    reg cap_en_d2;

    always @(posedge pclk or negedge rst_n) begin
        if (!rst_n) begin
            cap_en_d1 <= 1'b0;
            cap_en_d2 <= 1'b0;
        end else begin
            cap_en_d1 <= capture_enable;
            cap_en_d2 <= cap_en_d1;
        end
    end

    wire cap_en = cap_en_d2;

    
    wire axis_fire;
    assign axis_fire = m_axis_tvalid && m_axis_tready;

    wire can_load_new;
    assign can_load_new = (!m_axis_tvalid) || axis_fire;

    wire pixel_in_range;
    assign pixel_in_range =
        axis_frame_active &&
        pixel_valid &&
        (pixel_x < FRAME_WIDTH) &&
        (pixel_y < FRAME_HEIGHT);

    wire is_first_pixel;
    assign is_first_pixel =
        (pixel_x == 0) &&
        (pixel_y == 0);

    wire is_line_last;
    assign is_line_last =
        (pixel_x == FRAME_WIDTH - 1);

    wire is_frame_last;
    assign is_frame_last =
        (pixel_x == FRAME_WIDTH - 1) &&
        (pixel_y == FRAME_HEIGHT - 1);

    
    always @(posedge pclk or negedge rst_n) begin
        if (!rst_n) begin
            m_axis_tdata          <= 32'h00000000;
            m_axis_tvalid         <= 1'b0;
            m_axis_tlast          <= 1'b0;
            m_axis_tuser          <= 1'b0;

            axis_frame_active     <= 1'b0;
            axis_frame_done       <= 1'b0;
            axis_overflow         <= 1'b0;
            axis_sent_pixel_count <= 32'd0;
        end else begin
            axis_frame_done <= 1'b0;

            if (!cap_en) begin
                m_axis_tdata          <= 32'h00000000;
                m_axis_tvalid         <= 1'b0;
                m_axis_tlast          <= 1'b0;
                m_axis_tuser          <= 1'b0;

                axis_frame_active     <= 1'b0;
                axis_frame_done       <= 1'b0;
                axis_overflow         <= 1'b0;
                axis_sent_pixel_count <= 32'd0;
            end else begin

               
                if (frame_start) begin
                    axis_frame_active     <= 1'b1;
                    axis_frame_done       <= 1'b0;
                    axis_overflow         <= 1'b0;
                    axis_sent_pixel_count <= 32'd0;
                end

                if (can_load_new && pixel_in_range) begin
                    m_axis_tdata  <= {16'h0000, pixel_data};
                    m_axis_tvalid <= 1'b1;

                    if (is_first_pixel)
                        m_axis_tuser <= 1'b1;
                    else
                        m_axis_tuser <= 1'b0;

                    if (is_line_last)
                        m_axis_tlast <= 1'b1;
                    else
                        m_axis_tlast <= 1'b0;

                    axis_sent_pixel_count <= axis_sent_pixel_count + 1'b1;

                    if (is_frame_last) begin
                        axis_frame_done   <= 1'b1;
                        axis_frame_active <= 1'b0;
                    end
                end else begin
                    if (axis_fire) begin
                        m_axis_tvalid <= 1'b0;
                        m_axis_tlast  <= 1'b0;
                        m_axis_tuser  <= 1'b0;
                    end

                    if (m_axis_tvalid && !m_axis_tready && pixel_valid) begin
                        axis_overflow <= 1'b1;
                    end
                end
            end
        end
    end

endmodule