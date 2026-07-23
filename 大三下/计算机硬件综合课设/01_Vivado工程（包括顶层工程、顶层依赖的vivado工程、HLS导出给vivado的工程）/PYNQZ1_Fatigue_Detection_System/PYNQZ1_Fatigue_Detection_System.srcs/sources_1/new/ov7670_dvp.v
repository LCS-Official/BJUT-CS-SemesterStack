`timescale 1ns / 1ps

module ov7670_dvp #(
    parameter VSYNC_ACTIVE_LEVEL = 1'b1,
    parameter HREF_ACTIVE_LEVEL  = 1'b1,
    parameter SWAP_BYTES         = 1'b0,
    parameter X_BITS             = 11,
    parameter Y_BITS             = 10
)(
    input  wire                  pclk,
    input  wire                  rst_n,

    input  wire                  cam_vsync,
    input  wire                  cam_href,
    input  wire [7:0]            cam_data,

    output reg  [15:0]           pixel_data,
    output reg                   pixel_valid,

    output reg  [X_BITS-1:0]     pixel_x,
    output reg  [Y_BITS-1:0]     pixel_y,

    output reg                   frame_start,
    output reg                   line_start,
    output reg                   line_end,

    output reg                   frame_valid,
    output reg                   line_active,

    output reg  [7:0]            dbg_byte_data,
    output reg                   dbg_byte_valid,
    output reg                   dbg_byte_phase
);


    reg       vsync_q;
    reg       vsync_d;
    reg       href_q;
    reg       href_d;
    reg [7:0] data_q;

    wire vsync_active_now;
    wire vsync_active_pre;
    wire href_active_now;
    wire href_active_pre;

    assign vsync_active_now = (vsync_q == VSYNC_ACTIVE_LEVEL);
    assign vsync_active_pre = (vsync_d == VSYNC_ACTIVE_LEVEL);

    assign href_active_now  = (href_q  == HREF_ACTIVE_LEVEL);
    assign href_active_pre  = (href_d  == HREF_ACTIVE_LEVEL);

    wire vsync_active_rise;
    wire vsync_active_fall;
    wire href_active_rise;
    wire href_active_fall;

    assign vsync_active_rise = (!vsync_active_pre) && vsync_active_now;
    assign vsync_active_fall = vsync_active_pre && (!vsync_active_now);

    assign href_active_rise  = (!href_active_pre) && href_active_now;
    assign href_active_fall  = href_active_pre && (!href_active_now);

   
    wire current_frame_valid;
    wire current_line_active;
    wire current_byte_valid;

    assign current_frame_valid = !vsync_active_now;
    assign current_line_active = (!vsync_active_now) && href_active_now;
    assign current_byte_valid  = current_frame_valid && current_line_active;

    wire [7:0] sample_byte;
    assign sample_byte = data_q;

   

    reg [7:0] first_byte;
    reg       byte_phase;

    reg [X_BITS-1:0] x_cnt;
    reg [Y_BITS-1:0] y_cnt;
    reg              line_has_pixel;

    always @(posedge pclk or negedge rst_n) begin
        if (!rst_n) begin
            vsync_q        <= 1'b0;
            vsync_d        <= 1'b0;
            href_q         <= 1'b0;
            href_d         <= 1'b0;
            data_q         <= 8'h00;

            frame_start    <= 1'b0;
            line_start     <= 1'b0;
            line_end       <= 1'b0;
            frame_valid    <= 1'b0;
            line_active    <= 1'b0;

            first_byte     <= 8'h00;
            byte_phase     <= 1'b0;

            pixel_data     <= 16'h0000;
            pixel_valid    <= 1'b0;

            pixel_x        <= {X_BITS{1'b0}};
            pixel_y        <= {Y_BITS{1'b0}};
            x_cnt          <= {X_BITS{1'b0}};
            y_cnt          <= {Y_BITS{1'b0}};
            line_has_pixel <= 1'b0;

            dbg_byte_data  <= 8'h00;
            dbg_byte_valid <= 1'b0;
            dbg_byte_phase <= 1'b0;
        end else begin
           
            vsync_d <= vsync_q;
            href_d  <= href_q;

            vsync_q <= cam_vsync;
            href_q  <= cam_href;
            data_q  <= cam_data;

            frame_start    <= 1'b0;
            line_start     <= 1'b0;
            line_end       <= 1'b0;
            pixel_valid    <= 1'b0;
            dbg_byte_valid <= 1'b0;

            frame_valid    <= current_frame_valid;
            line_active    <= current_line_active;

           
            if (vsync_active_fall) begin
                frame_start    <= 1'b1;

                x_cnt          <= {X_BITS{1'b0}};
                y_cnt          <= {Y_BITS{1'b0}};
                pixel_x        <= {X_BITS{1'b0}};
                pixel_y        <= {Y_BITS{1'b0}};

                first_byte     <= 8'h00;
                byte_phase     <= 1'b0;
                line_has_pixel <= 1'b0;
            end

            
            if (vsync_active_now) begin
                first_byte     <= 8'h00;
                byte_phase     <= 1'b0;
                line_has_pixel <= 1'b0;
            end else begin

               
                if (href_active_rise) begin
                    line_start     <= 1'b1;
                    x_cnt          <= {X_BITS{1'b0}};
                    first_byte     <= 8'h00;
                    byte_phase     <= 1'b0;
                    line_has_pixel <= 1'b0;
                end

                
                if (href_active_fall) begin
                    line_end   <= 1'b1;
                    x_cnt      <= {X_BITS{1'b0}};
                    first_byte <= 8'h00;
                    byte_phase <= 1'b0;

                    if (line_has_pixel) begin
                        y_cnt <= y_cnt + 1'b1;
                    end

                    line_has_pixel <= 1'b0;
                end

               
                if (current_byte_valid) begin
                    dbg_byte_data  <= sample_byte;
                    dbg_byte_valid <= 1'b1;

                    if (byte_phase == 1'b0) begin
                        first_byte     <= sample_byte;
                        byte_phase     <= 1'b1;
                        dbg_byte_phase <= 1'b1;
                    end else begin
                        if (SWAP_BYTES) begin
                            pixel_data <= {sample_byte, first_byte};
                        end else begin
                            pixel_data <= {first_byte, sample_byte};
                        end

                        pixel_valid    <= 1'b1;
                        pixel_x        <= x_cnt;
                        pixel_y        <= y_cnt;

                        x_cnt          <= x_cnt + 1'b1;
                        line_has_pixel <= 1'b1;

                        byte_phase     <= 1'b0;
                        dbg_byte_phase <= 1'b0;
                    end
                end
            end
        end
    end

endmodule