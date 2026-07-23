// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2023.2 (64-bit)
// Tool Version Limit: 2023.10
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
/***************************** Include Files *********************************/
#include "xclassify.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XClassify_CfgInitialize(XClassify *InstancePtr, XClassify_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Ctrl_BaseAddress = ConfigPtr->Ctrl_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XClassify_Start(XClassify *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XClassify_ReadReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_AP_CTRL) & 0x80;
    XClassify_WriteReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XClassify_IsDone(XClassify *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XClassify_ReadReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XClassify_IsIdle(XClassify *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XClassify_ReadReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XClassify_IsReady(XClassify *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XClassify_ReadReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XClassify_EnableAutoRestart(XClassify *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XClassify_WriteReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_AP_CTRL, 0x80);
}

void XClassify_DisableAutoRestart(XClassify *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XClassify_WriteReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_AP_CTRL, 0);
}

void XClassify_Set_threshold_q(XClassify *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XClassify_WriteReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_THRESHOLD_Q_DATA, Data);
}

u32 XClassify_Get_threshold_q(XClassify *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XClassify_ReadReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_THRESHOLD_Q_DATA);
    return Data;
}

void XClassify_InterruptGlobalEnable(XClassify *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XClassify_WriteReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_GIE, 1);
}

void XClassify_InterruptGlobalDisable(XClassify *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XClassify_WriteReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_GIE, 0);
}

void XClassify_InterruptEnable(XClassify *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XClassify_ReadReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_IER);
    XClassify_WriteReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_IER, Register | Mask);
}

void XClassify_InterruptDisable(XClassify *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XClassify_ReadReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_IER);
    XClassify_WriteReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_IER, Register & (~Mask));
}

void XClassify_InterruptClear(XClassify *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XClassify_WriteReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_ISR, Mask);
}

u32 XClassify_InterruptGetEnabled(XClassify *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XClassify_ReadReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_IER);
}

u32 XClassify_InterruptGetStatus(XClassify *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XClassify_ReadReg(InstancePtr->Ctrl_BaseAddress, XCLASSIFY_CTRL_ADDR_ISR);
}

