// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2023.2 (64-bit)
// Tool Version Limit: 2023.10
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
/***************************** Include Files *********************************/
#include "xeye_feature.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XEye_feature_CfgInitialize(XEye_feature *InstancePtr, XEye_feature_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Ctrl_BaseAddress = ConfigPtr->Ctrl_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XEye_feature_Start(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_AP_CTRL) & 0x80;
    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XEye_feature_IsDone(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XEye_feature_IsIdle(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XEye_feature_IsReady(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XEye_feature_EnableAutoRestart(XEye_feature *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_AP_CTRL, 0x80);
}

void XEye_feature_DisableAutoRestart(XEye_feature *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_AP_CTRL, 0);
}

void XEye_feature_Set_frame_width(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_FRAME_WIDTH_DATA, Data);
}

u32 XEye_feature_Get_frame_width(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_FRAME_WIDTH_DATA);
    return Data;
}

void XEye_feature_Set_frame_height(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_FRAME_HEIGHT_DATA, Data);
}

u32 XEye_feature_Get_frame_height(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_FRAME_HEIGHT_DATA);
    return Data;
}

void XEye_feature_Set_left_x(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_LEFT_X_DATA, Data);
}

u32 XEye_feature_Get_left_x(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_LEFT_X_DATA);
    return Data;
}

void XEye_feature_Set_left_y(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_LEFT_Y_DATA, Data);
}

u32 XEye_feature_Get_left_y(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_LEFT_Y_DATA);
    return Data;
}

void XEye_feature_Set_left_w(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_LEFT_W_DATA, Data);
}

u32 XEye_feature_Get_left_w(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_LEFT_W_DATA);
    return Data;
}

void XEye_feature_Set_left_h(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_LEFT_H_DATA, Data);
}

u32 XEye_feature_Get_left_h(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_LEFT_H_DATA);
    return Data;
}

void XEye_feature_Set_right_x(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_RIGHT_X_DATA, Data);
}

u32 XEye_feature_Get_right_x(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_RIGHT_X_DATA);
    return Data;
}

void XEye_feature_Set_right_y(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_RIGHT_Y_DATA, Data);
}

u32 XEye_feature_Get_right_y(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_RIGHT_Y_DATA);
    return Data;
}

void XEye_feature_Set_right_w(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_RIGHT_W_DATA, Data);
}

u32 XEye_feature_Get_right_w(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_RIGHT_W_DATA);
    return Data;
}

void XEye_feature_Set_right_h(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_RIGHT_H_DATA, Data);
}

u32 XEye_feature_Get_right_h(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_RIGHT_H_DATA);
    return Data;
}

void XEye_feature_Set_roi_valid(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_ROI_VALID_DATA, Data);
}

u32 XEye_feature_Get_roi_valid(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_ROI_VALID_DATA);
    return Data;
}

void XEye_feature_Set_fixed_thresh(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_FIXED_THRESH_DATA, Data);
}

u32 XEye_feature_Get_fixed_thresh(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_FIXED_THRESH_DATA);
    return Data;
}

void XEye_feature_Set_adapt_offset(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_ADAPT_OFFSET_DATA, Data);
}

u32 XEye_feature_Get_adapt_offset(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_ADAPT_OFFSET_DATA);
    return Data;
}

void XEye_feature_Set_fixed_scale(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_FIXED_SCALE_DATA, Data);
}

u32 XEye_feature_Get_fixed_scale(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_FIXED_SCALE_DATA);
    return Data;
}

void XEye_feature_Set_pixel_format(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_PIXEL_FORMAT_DATA, Data);
}

u32 XEye_feature_Get_pixel_format(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_PIXEL_FORMAT_DATA);
    return Data;
}

void XEye_feature_Set_roi_version(XEye_feature *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_ROI_VERSION_DATA, Data);
}

u32 XEye_feature_Get_roi_version(XEye_feature *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_ROI_VERSION_DATA);
    return Data;
}

void XEye_feature_InterruptGlobalEnable(XEye_feature *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_GIE, 1);
}

void XEye_feature_InterruptGlobalDisable(XEye_feature *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_GIE, 0);
}

void XEye_feature_InterruptEnable(XEye_feature *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_IER);
    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_IER, Register | Mask);
}

void XEye_feature_InterruptDisable(XEye_feature *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_IER);
    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_IER, Register & (~Mask));
}

void XEye_feature_InterruptClear(XEye_feature *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XEye_feature_WriteReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_ISR, Mask);
}

u32 XEye_feature_InterruptGetEnabled(XEye_feature *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_IER);
}

u32 XEye_feature_InterruptGetStatus(XEye_feature *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XEye_feature_ReadReg(InstancePtr->Ctrl_BaseAddress, XEYE_FEATURE_CTRL_ADDR_ISR);
}

