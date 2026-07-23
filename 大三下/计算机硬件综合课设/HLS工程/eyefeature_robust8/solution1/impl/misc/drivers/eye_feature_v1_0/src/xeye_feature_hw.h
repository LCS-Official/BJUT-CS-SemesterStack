// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2023.2 (64-bit)
// Tool Version Limit: 2023.10
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
// CTRL
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

#define XEYE_FEATURE_CTRL_ADDR_AP_CTRL           0x00
#define XEYE_FEATURE_CTRL_ADDR_GIE               0x04
#define XEYE_FEATURE_CTRL_ADDR_IER               0x08
#define XEYE_FEATURE_CTRL_ADDR_ISR               0x0c
#define XEYE_FEATURE_CTRL_ADDR_FRAME_WIDTH_DATA  0x10
#define XEYE_FEATURE_CTRL_BITS_FRAME_WIDTH_DATA  32
#define XEYE_FEATURE_CTRL_ADDR_FRAME_HEIGHT_DATA 0x18
#define XEYE_FEATURE_CTRL_BITS_FRAME_HEIGHT_DATA 32
#define XEYE_FEATURE_CTRL_ADDR_LEFT_X_DATA       0x20
#define XEYE_FEATURE_CTRL_BITS_LEFT_X_DATA       32
#define XEYE_FEATURE_CTRL_ADDR_LEFT_Y_DATA       0x28
#define XEYE_FEATURE_CTRL_BITS_LEFT_Y_DATA       32
#define XEYE_FEATURE_CTRL_ADDR_LEFT_W_DATA       0x30
#define XEYE_FEATURE_CTRL_BITS_LEFT_W_DATA       32
#define XEYE_FEATURE_CTRL_ADDR_LEFT_H_DATA       0x38
#define XEYE_FEATURE_CTRL_BITS_LEFT_H_DATA       32
#define XEYE_FEATURE_CTRL_ADDR_RIGHT_X_DATA      0x40
#define XEYE_FEATURE_CTRL_BITS_RIGHT_X_DATA      32
#define XEYE_FEATURE_CTRL_ADDR_RIGHT_Y_DATA      0x48
#define XEYE_FEATURE_CTRL_BITS_RIGHT_Y_DATA      32
#define XEYE_FEATURE_CTRL_ADDR_RIGHT_W_DATA      0x50
#define XEYE_FEATURE_CTRL_BITS_RIGHT_W_DATA      32
#define XEYE_FEATURE_CTRL_ADDR_RIGHT_H_DATA      0x58
#define XEYE_FEATURE_CTRL_BITS_RIGHT_H_DATA      32
#define XEYE_FEATURE_CTRL_ADDR_ROI_VALID_DATA    0x60
#define XEYE_FEATURE_CTRL_BITS_ROI_VALID_DATA    32
#define XEYE_FEATURE_CTRL_ADDR_FIXED_THRESH_DATA 0x68
#define XEYE_FEATURE_CTRL_BITS_FIXED_THRESH_DATA 32
#define XEYE_FEATURE_CTRL_ADDR_ADAPT_OFFSET_DATA 0x70
#define XEYE_FEATURE_CTRL_BITS_ADAPT_OFFSET_DATA 32
#define XEYE_FEATURE_CTRL_ADDR_FIXED_SCALE_DATA  0x78
#define XEYE_FEATURE_CTRL_BITS_FIXED_SCALE_DATA  32
#define XEYE_FEATURE_CTRL_ADDR_PIXEL_FORMAT_DATA 0x80
#define XEYE_FEATURE_CTRL_BITS_PIXEL_FORMAT_DATA 32
#define XEYE_FEATURE_CTRL_ADDR_ROI_VERSION_DATA  0x88
#define XEYE_FEATURE_CTRL_BITS_ROI_VERSION_DATA  32

