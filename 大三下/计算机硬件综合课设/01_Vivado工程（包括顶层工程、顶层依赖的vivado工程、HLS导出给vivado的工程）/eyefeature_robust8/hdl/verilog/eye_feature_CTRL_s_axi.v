// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2023.2 (64-bit)
// Tool Version Limit: 2023.10
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
`timescale 1ns/1ps
module eye_feature_CTRL_s_axi
#(parameter
    C_S_AXI_ADDR_WIDTH = 8,
    C_S_AXI_DATA_WIDTH = 32
)(
    input  wire                          ACLK,
    input  wire                          ARESET,
    input  wire                          ACLK_EN,
    input  wire [C_S_AXI_ADDR_WIDTH-1:0] AWADDR,
    input  wire                          AWVALID,
    output wire                          AWREADY,
    input  wire [C_S_AXI_DATA_WIDTH-1:0] WDATA,
    input  wire [C_S_AXI_DATA_WIDTH/8-1:0] WSTRB,
    input  wire                          WVALID,
    output wire                          WREADY,
    output wire [1:0]                    BRESP,
    output wire                          BVALID,
    input  wire                          BREADY,
    input  wire [C_S_AXI_ADDR_WIDTH-1:0] ARADDR,
    input  wire                          ARVALID,
    output wire                          ARREADY,
    output wire [C_S_AXI_DATA_WIDTH-1:0] RDATA,
    output wire [1:0]                    RRESP,
    output wire                          RVALID,
    input  wire                          RREADY,
    output wire                          interrupt,
    output wire [31:0]                   frame_width,
    output wire [31:0]                   frame_height,
    output wire [31:0]                   left_x,
    output wire [31:0]                   left_y,
    output wire [31:0]                   left_w,
    output wire [31:0]                   left_h,
    output wire [31:0]                   right_x,
    output wire [31:0]                   right_y,
    output wire [31:0]                   right_w,
    output wire [31:0]                   right_h,
    output wire [31:0]                   roi_valid,
    output wire [31:0]                   fixed_thresh,
    output wire [31:0]                   adapt_offset,
    output wire [31:0]                   fixed_scale,
    output wire [31:0]                   pixel_format,
    output wire [31:0]                   roi_version,
    output wire                          ap_start,
    input  wire                          ap_done,
    input  wire                          ap_ready,
    input  wire                          ap_idle
);
//------------------------Address Info-------------------
// Protocol Used: ap_ctrl_hs
//
// 0x00 : Control signals
//        bit 0  - ap_start (Read/Write/COH)
//        bit 1  - ap_done (Read/COR)
//        bit 2  - ap_idle (Read)
//        bit 3  - ap_ready (Read/COR)
//        bit 7  - auto_restart (Read/Write)
//        bit 9  - interrupt (Read)
//        others - reserved
// 0x04 : Global Interrupt Enable Register
//        bit 0  - Global Interrupt Enable (Read/Write)
//        others - reserved
// 0x08 : IP Interrupt Enable Register (Read/Write)
//        bit 0 - enable ap_done interrupt (Read/Write)
//        bit 1 - enable ap_ready interrupt (Read/Write)
//        others - reserved
// 0x0c : IP Interrupt Status Register (Read/TOW)
//        bit 0 - ap_done (Read/TOW)
//        bit 1 - ap_ready (Read/TOW)
//        others - reserved
// 0x10 : Data signal of frame_width
//        bit 31~0 - frame_width[31:0] (Read/Write)
// 0x14 : reserved
// 0x18 : Data signal of frame_height
//        bit 31~0 - frame_height[31:0] (Read/Write)
// 0x1c : reserved
// 0x20 : Data signal of left_x
//        bit 31~0 - left_x[31:0] (Read/Write)
// 0x24 : reserved
// 0x28 : Data signal of left_y
//        bit 31~0 - left_y[31:0] (Read/Write)
// 0x2c : reserved
// 0x30 : Data signal of left_w
//        bit 31~0 - left_w[31:0] (Read/Write)
// 0x34 : reserved
// 0x38 : Data signal of left_h
//        bit 31~0 - left_h[31:0] (Read/Write)
// 0x3c : reserved
// 0x40 : Data signal of right_x
//        bit 31~0 - right_x[31:0] (Read/Write)
// 0x44 : reserved
// 0x48 : Data signal of right_y
//        bit 31~0 - right_y[31:0] (Read/Write)
// 0x4c : reserved
// 0x50 : Data signal of right_w
//        bit 31~0 - right_w[31:0] (Read/Write)
// 0x54 : reserved
// 0x58 : Data signal of right_h
//        bit 31~0 - right_h[31:0] (Read/Write)
// 0x5c : reserved
// 0x60 : Data signal of roi_valid
//        bit 31~0 - roi_valid[31:0] (Read/Write)
// 0x64 : reserved
// 0x68 : Data signal of fixed_thresh
//        bit 31~0 - fixed_thresh[31:0] (Read/Write)
// 0x6c : reserved
// 0x70 : Data signal of adapt_offset
//        bit 31~0 - adapt_offset[31:0] (Read/Write)
// 0x74 : reserved
// 0x78 : Data signal of fixed_scale
//        bit 31~0 - fixed_scale[31:0] (Read/Write)
// 0x7c : reserved
// 0x80 : Data signal of pixel_format
//        bit 31~0 - pixel_format[31:0] (Read/Write)
// 0x84 : reserved
// 0x88 : Data signal of roi_version
//        bit 31~0 - roi_version[31:0] (Read/Write)
// 0x8c : reserved
// (SC = Self Clear, COR = Clear on Read, TOW = Toggle on Write, COH = Clear on Handshake)

//------------------------Parameter----------------------
localparam
    ADDR_AP_CTRL             = 8'h00,
    ADDR_GIE                 = 8'h04,
    ADDR_IER                 = 8'h08,
    ADDR_ISR                 = 8'h0c,
    ADDR_FRAME_WIDTH_DATA_0  = 8'h10,
    ADDR_FRAME_WIDTH_CTRL    = 8'h14,
    ADDR_FRAME_HEIGHT_DATA_0 = 8'h18,
    ADDR_FRAME_HEIGHT_CTRL   = 8'h1c,
    ADDR_LEFT_X_DATA_0       = 8'h20,
    ADDR_LEFT_X_CTRL         = 8'h24,
    ADDR_LEFT_Y_DATA_0       = 8'h28,
    ADDR_LEFT_Y_CTRL         = 8'h2c,
    ADDR_LEFT_W_DATA_0       = 8'h30,
    ADDR_LEFT_W_CTRL         = 8'h34,
    ADDR_LEFT_H_DATA_0       = 8'h38,
    ADDR_LEFT_H_CTRL         = 8'h3c,
    ADDR_RIGHT_X_DATA_0      = 8'h40,
    ADDR_RIGHT_X_CTRL        = 8'h44,
    ADDR_RIGHT_Y_DATA_0      = 8'h48,
    ADDR_RIGHT_Y_CTRL        = 8'h4c,
    ADDR_RIGHT_W_DATA_0      = 8'h50,
    ADDR_RIGHT_W_CTRL        = 8'h54,
    ADDR_RIGHT_H_DATA_0      = 8'h58,
    ADDR_RIGHT_H_CTRL        = 8'h5c,
    ADDR_ROI_VALID_DATA_0    = 8'h60,
    ADDR_ROI_VALID_CTRL      = 8'h64,
    ADDR_FIXED_THRESH_DATA_0 = 8'h68,
    ADDR_FIXED_THRESH_CTRL   = 8'h6c,
    ADDR_ADAPT_OFFSET_DATA_0 = 8'h70,
    ADDR_ADAPT_OFFSET_CTRL   = 8'h74,
    ADDR_FIXED_SCALE_DATA_0  = 8'h78,
    ADDR_FIXED_SCALE_CTRL    = 8'h7c,
    ADDR_PIXEL_FORMAT_DATA_0 = 8'h80,
    ADDR_PIXEL_FORMAT_CTRL   = 8'h84,
    ADDR_ROI_VERSION_DATA_0  = 8'h88,
    ADDR_ROI_VERSION_CTRL    = 8'h8c,
    WRIDLE                   = 2'd0,
    WRDATA                   = 2'd1,
    WRRESP                   = 2'd2,
    WRRESET                  = 2'd3,
    RDIDLE                   = 2'd0,
    RDDATA                   = 2'd1,
    RDRESET                  = 2'd2,
    ADDR_BITS                = 8;

//------------------------Local signal-------------------
    reg  [1:0]                    wstate = WRRESET;
    reg  [1:0]                    wnext;
    reg  [ADDR_BITS-1:0]          waddr;
    wire [C_S_AXI_DATA_WIDTH-1:0] wmask;
    wire                          aw_hs;
    wire                          w_hs;
    reg  [1:0]                    rstate = RDRESET;
    reg  [1:0]                    rnext;
    reg  [C_S_AXI_DATA_WIDTH-1:0] rdata;
    wire                          ar_hs;
    wire [ADDR_BITS-1:0]          raddr;
    // internal registers
    reg                           int_ap_idle;
    reg                           int_ap_ready = 1'b0;
    wire                          task_ap_ready;
    reg                           int_ap_done = 1'b0;
    wire                          task_ap_done;
    reg                           int_task_ap_done = 1'b0;
    reg                           int_ap_start = 1'b0;
    reg                           int_interrupt = 1'b0;
    reg                           int_auto_restart = 1'b0;
    reg                           auto_restart_status = 1'b0;
    wire                          auto_restart_done;
    reg                           int_gie = 1'b0;
    reg  [1:0]                    int_ier = 2'b0;
    reg  [1:0]                    int_isr = 2'b0;
    reg  [31:0]                   int_frame_width = 'b0;
    reg  [31:0]                   int_frame_height = 'b0;
    reg  [31:0]                   int_left_x = 'b0;
    reg  [31:0]                   int_left_y = 'b0;
    reg  [31:0]                   int_left_w = 'b0;
    reg  [31:0]                   int_left_h = 'b0;
    reg  [31:0]                   int_right_x = 'b0;
    reg  [31:0]                   int_right_y = 'b0;
    reg  [31:0]                   int_right_w = 'b0;
    reg  [31:0]                   int_right_h = 'b0;
    reg  [31:0]                   int_roi_valid = 'b0;
    reg  [31:0]                   int_fixed_thresh = 'b0;
    reg  [31:0]                   int_adapt_offset = 'b0;
    reg  [31:0]                   int_fixed_scale = 'b0;
    reg  [31:0]                   int_pixel_format = 'b0;
    reg  [31:0]                   int_roi_version = 'b0;

//------------------------Instantiation------------------


//------------------------AXI write fsm------------------
assign AWREADY = (wstate == WRIDLE);
assign WREADY  = (wstate == WRDATA);
assign BRESP   = 2'b00;  // OKAY
assign BVALID  = (wstate == WRRESP);
assign wmask   = { {8{WSTRB[3]}}, {8{WSTRB[2]}}, {8{WSTRB[1]}}, {8{WSTRB[0]}} };
assign aw_hs   = AWVALID & AWREADY;
assign w_hs    = WVALID & WREADY;

// wstate
always @(posedge ACLK) begin
    if (ARESET)
        wstate <= WRRESET;
    else if (ACLK_EN)
        wstate <= wnext;
end

// wnext
always @(*) begin
    case (wstate)
        WRIDLE:
            if (AWVALID)
                wnext = WRDATA;
            else
                wnext = WRIDLE;
        WRDATA:
            if (WVALID)
                wnext = WRRESP;
            else
                wnext = WRDATA;
        WRRESP:
            if (BREADY)
                wnext = WRIDLE;
            else
                wnext = WRRESP;
        default:
            wnext = WRIDLE;
    endcase
end

// waddr
always @(posedge ACLK) begin
    if (ACLK_EN) begin
        if (aw_hs)
            waddr <= AWADDR[ADDR_BITS-1:0];
    end
end

//------------------------AXI read fsm-------------------
assign ARREADY = (rstate == RDIDLE);
assign RDATA   = rdata;
assign RRESP   = 2'b00;  // OKAY
assign RVALID  = (rstate == RDDATA);
assign ar_hs   = ARVALID & ARREADY;
assign raddr   = ARADDR[ADDR_BITS-1:0];

// rstate
always @(posedge ACLK) begin
    if (ARESET)
        rstate <= RDRESET;
    else if (ACLK_EN)
        rstate <= rnext;
end

// rnext
always @(*) begin
    case (rstate)
        RDIDLE:
            if (ARVALID)
                rnext = RDDATA;
            else
                rnext = RDIDLE;
        RDDATA:
            if (RREADY & RVALID)
                rnext = RDIDLE;
            else
                rnext = RDDATA;
        default:
            rnext = RDIDLE;
    endcase
end

// rdata
always @(posedge ACLK) begin
    if (ACLK_EN) begin
        if (ar_hs) begin
            rdata <= 'b0;
            case (raddr)
                ADDR_AP_CTRL: begin
                    rdata[0] <= int_ap_start;
                    rdata[1] <= int_task_ap_done;
                    rdata[2] <= int_ap_idle;
                    rdata[3] <= int_ap_ready;
                    rdata[7] <= int_auto_restart;
                    rdata[9] <= int_interrupt;
                end
                ADDR_GIE: begin
                    rdata <= int_gie;
                end
                ADDR_IER: begin
                    rdata <= int_ier;
                end
                ADDR_ISR: begin
                    rdata <= int_isr;
                end
                ADDR_FRAME_WIDTH_DATA_0: begin
                    rdata <= int_frame_width[31:0];
                end
                ADDR_FRAME_HEIGHT_DATA_0: begin
                    rdata <= int_frame_height[31:0];
                end
                ADDR_LEFT_X_DATA_0: begin
                    rdata <= int_left_x[31:0];
                end
                ADDR_LEFT_Y_DATA_0: begin
                    rdata <= int_left_y[31:0];
                end
                ADDR_LEFT_W_DATA_0: begin
                    rdata <= int_left_w[31:0];
                end
                ADDR_LEFT_H_DATA_0: begin
                    rdata <= int_left_h[31:0];
                end
                ADDR_RIGHT_X_DATA_0: begin
                    rdata <= int_right_x[31:0];
                end
                ADDR_RIGHT_Y_DATA_0: begin
                    rdata <= int_right_y[31:0];
                end
                ADDR_RIGHT_W_DATA_0: begin
                    rdata <= int_right_w[31:0];
                end
                ADDR_RIGHT_H_DATA_0: begin
                    rdata <= int_right_h[31:0];
                end
                ADDR_ROI_VALID_DATA_0: begin
                    rdata <= int_roi_valid[31:0];
                end
                ADDR_FIXED_THRESH_DATA_0: begin
                    rdata <= int_fixed_thresh[31:0];
                end
                ADDR_ADAPT_OFFSET_DATA_0: begin
                    rdata <= int_adapt_offset[31:0];
                end
                ADDR_FIXED_SCALE_DATA_0: begin
                    rdata <= int_fixed_scale[31:0];
                end
                ADDR_PIXEL_FORMAT_DATA_0: begin
                    rdata <= int_pixel_format[31:0];
                end
                ADDR_ROI_VERSION_DATA_0: begin
                    rdata <= int_roi_version[31:0];
                end
            endcase
        end
    end
end


//------------------------Register logic-----------------
assign interrupt         = int_interrupt;
assign ap_start          = int_ap_start;
assign task_ap_done      = (ap_done && !auto_restart_status) || auto_restart_done;
assign task_ap_ready     = ap_ready && !int_auto_restart;
assign auto_restart_done = auto_restart_status && (ap_idle && !int_ap_idle);
assign frame_width       = int_frame_width;
assign frame_height      = int_frame_height;
assign left_x            = int_left_x;
assign left_y            = int_left_y;
assign left_w            = int_left_w;
assign left_h            = int_left_h;
assign right_x           = int_right_x;
assign right_y           = int_right_y;
assign right_w           = int_right_w;
assign right_h           = int_right_h;
assign roi_valid         = int_roi_valid;
assign fixed_thresh      = int_fixed_thresh;
assign adapt_offset      = int_adapt_offset;
assign fixed_scale       = int_fixed_scale;
assign pixel_format      = int_pixel_format;
assign roi_version       = int_roi_version;
// int_interrupt
always @(posedge ACLK) begin
    if (ARESET)
        int_interrupt <= 1'b0;
    else if (ACLK_EN) begin
        if (int_gie && (|int_isr))
            int_interrupt <= 1'b1;
        else
            int_interrupt <= 1'b0;
    end
end

// int_ap_start
always @(posedge ACLK) begin
    if (ARESET)
        int_ap_start <= 1'b0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_AP_CTRL && WSTRB[0] && WDATA[0])
            int_ap_start <= 1'b1;
        else if (ap_ready)
            int_ap_start <= int_auto_restart; // clear on handshake/auto restart
    end
end

// int_ap_done
always @(posedge ACLK) begin
    if (ARESET)
        int_ap_done <= 1'b0;
    else if (ACLK_EN) begin
            int_ap_done <= ap_done;
    end
end

// int_task_ap_done
always @(posedge ACLK) begin
    if (ARESET)
        int_task_ap_done <= 1'b0;
    else if (ACLK_EN) begin
        if (task_ap_done)
            int_task_ap_done <= 1'b1;
        else if (ar_hs && raddr == ADDR_AP_CTRL)
            int_task_ap_done <= 1'b0; // clear on read
    end
end

// int_ap_idle
always @(posedge ACLK) begin
    if (ARESET)
        int_ap_idle <= 1'b0;
    else if (ACLK_EN) begin
            int_ap_idle <= ap_idle;
    end
end

// int_ap_ready
always @(posedge ACLK) begin
    if (ARESET)
        int_ap_ready <= 1'b0;
    else if (ACLK_EN) begin
        if (task_ap_ready)
            int_ap_ready <= 1'b1;
        else if (ar_hs && raddr == ADDR_AP_CTRL)
            int_ap_ready <= 1'b0;
    end
end

// int_auto_restart
always @(posedge ACLK) begin
    if (ARESET)
        int_auto_restart <= 1'b0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_AP_CTRL && WSTRB[0])
            int_auto_restart <=  WDATA[7];
    end
end

// auto_restart_status
always @(posedge ACLK) begin
    if (ARESET)
        auto_restart_status <= 1'b0;
    else if (ACLK_EN) begin
        if (int_auto_restart)
            auto_restart_status <= 1'b1;
        else if (ap_idle)
            auto_restart_status <= 1'b0;
    end
end

// int_gie
always @(posedge ACLK) begin
    if (ARESET)
        int_gie <= 1'b0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_GIE && WSTRB[0])
            int_gie <= WDATA[0];
    end
end

// int_ier
always @(posedge ACLK) begin
    if (ARESET)
        int_ier <= 1'b0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_IER && WSTRB[0])
            int_ier <= WDATA[1:0];
    end
end

// int_isr[0]
always @(posedge ACLK) begin
    if (ARESET)
        int_isr[0] <= 1'b0;
    else if (ACLK_EN) begin
        if (int_ier[0] & ap_done)
            int_isr[0] <= 1'b1;
        else if (w_hs && waddr == ADDR_ISR && WSTRB[0])
            int_isr[0] <= int_isr[0] ^ WDATA[0]; // toggle on write
    end
end

// int_isr[1]
always @(posedge ACLK) begin
    if (ARESET)
        int_isr[1] <= 1'b0;
    else if (ACLK_EN) begin
        if (int_ier[1] & ap_ready)
            int_isr[1] <= 1'b1;
        else if (w_hs && waddr == ADDR_ISR && WSTRB[0])
            int_isr[1] <= int_isr[1] ^ WDATA[1]; // toggle on write
    end
end

// int_frame_width[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_frame_width[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_FRAME_WIDTH_DATA_0)
            int_frame_width[31:0] <= (WDATA[31:0] & wmask) | (int_frame_width[31:0] & ~wmask);
    end
end

// int_frame_height[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_frame_height[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_FRAME_HEIGHT_DATA_0)
            int_frame_height[31:0] <= (WDATA[31:0] & wmask) | (int_frame_height[31:0] & ~wmask);
    end
end

// int_left_x[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_left_x[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_LEFT_X_DATA_0)
            int_left_x[31:0] <= (WDATA[31:0] & wmask) | (int_left_x[31:0] & ~wmask);
    end
end

// int_left_y[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_left_y[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_LEFT_Y_DATA_0)
            int_left_y[31:0] <= (WDATA[31:0] & wmask) | (int_left_y[31:0] & ~wmask);
    end
end

// int_left_w[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_left_w[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_LEFT_W_DATA_0)
            int_left_w[31:0] <= (WDATA[31:0] & wmask) | (int_left_w[31:0] & ~wmask);
    end
end

// int_left_h[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_left_h[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_LEFT_H_DATA_0)
            int_left_h[31:0] <= (WDATA[31:0] & wmask) | (int_left_h[31:0] & ~wmask);
    end
end

// int_right_x[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_right_x[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_RIGHT_X_DATA_0)
            int_right_x[31:0] <= (WDATA[31:0] & wmask) | (int_right_x[31:0] & ~wmask);
    end
end

// int_right_y[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_right_y[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_RIGHT_Y_DATA_0)
            int_right_y[31:0] <= (WDATA[31:0] & wmask) | (int_right_y[31:0] & ~wmask);
    end
end

// int_right_w[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_right_w[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_RIGHT_W_DATA_0)
            int_right_w[31:0] <= (WDATA[31:0] & wmask) | (int_right_w[31:0] & ~wmask);
    end
end

// int_right_h[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_right_h[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_RIGHT_H_DATA_0)
            int_right_h[31:0] <= (WDATA[31:0] & wmask) | (int_right_h[31:0] & ~wmask);
    end
end

// int_roi_valid[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_roi_valid[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_ROI_VALID_DATA_0)
            int_roi_valid[31:0] <= (WDATA[31:0] & wmask) | (int_roi_valid[31:0] & ~wmask);
    end
end

// int_fixed_thresh[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_fixed_thresh[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_FIXED_THRESH_DATA_0)
            int_fixed_thresh[31:0] <= (WDATA[31:0] & wmask) | (int_fixed_thresh[31:0] & ~wmask);
    end
end

// int_adapt_offset[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_adapt_offset[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_ADAPT_OFFSET_DATA_0)
            int_adapt_offset[31:0] <= (WDATA[31:0] & wmask) | (int_adapt_offset[31:0] & ~wmask);
    end
end

// int_fixed_scale[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_fixed_scale[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_FIXED_SCALE_DATA_0)
            int_fixed_scale[31:0] <= (WDATA[31:0] & wmask) | (int_fixed_scale[31:0] & ~wmask);
    end
end

// int_pixel_format[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_pixel_format[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_PIXEL_FORMAT_DATA_0)
            int_pixel_format[31:0] <= (WDATA[31:0] & wmask) | (int_pixel_format[31:0] & ~wmask);
    end
end

// int_roi_version[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_roi_version[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_ROI_VERSION_DATA_0)
            int_roi_version[31:0] <= (WDATA[31:0] & wmask) | (int_roi_version[31:0] & ~wmask);
    end
end

//synthesis translate_off
always @(posedge ACLK) begin
    if (ACLK_EN) begin
        if (int_gie & ~int_isr[0] & int_ier[0] & ap_done)
            $display ("// Interrupt Monitor : interrupt for ap_done detected @ \"%0t\"", $time);
        if (int_gie & ~int_isr[1] & int_ier[1] & ap_ready)
            $display ("// Interrupt Monitor : interrupt for ap_ready detected @ \"%0t\"", $time);
    end
end
//synthesis translate_on

//------------------------Memory logic-------------------

endmodule
