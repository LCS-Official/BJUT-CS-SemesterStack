// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2023.2 (64-bit)
// Tool Version Limit: 2023.10
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef XEYE_FEATURE_H
#define XEYE_FEATURE_H

#ifdef __cplusplus
extern "C" {
#endif

/***************************** Include Files *********************************/
#ifndef __linux__
#include "xil_types.h"
#include "xil_assert.h"
#include "xstatus.h"
#include "xil_io.h"
#else
#include <stdint.h>
#include <assert.h>
#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stddef.h>
#endif
#include "xeye_feature_hw.h"

/**************************** Type Definitions ******************************/
#ifdef __linux__
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
#else
typedef struct {
#ifdef SDT
    char *Name;
#else
    u16 DeviceId;
#endif
    u64 Ctrl_BaseAddress;
} XEye_feature_Config;
#endif

typedef struct {
    u64 Ctrl_BaseAddress;
    u32 IsReady;
} XEye_feature;

typedef u32 word_type;

/***************** Macros (Inline Functions) Definitions *********************/
#ifndef __linux__
#define XEye_feature_WriteReg(BaseAddress, RegOffset, Data) \
    Xil_Out32((BaseAddress) + (RegOffset), (u32)(Data))
#define XEye_feature_ReadReg(BaseAddress, RegOffset) \
    Xil_In32((BaseAddress) + (RegOffset))
#else
#define XEye_feature_WriteReg(BaseAddress, RegOffset, Data) \
    *(volatile u32*)((BaseAddress) + (RegOffset)) = (u32)(Data)
#define XEye_feature_ReadReg(BaseAddress, RegOffset) \
    *(volatile u32*)((BaseAddress) + (RegOffset))

#define Xil_AssertVoid(expr)    assert(expr)
#define Xil_AssertNonvoid(expr) assert(expr)

#define XST_SUCCESS             0
#define XST_DEVICE_NOT_FOUND    2
#define XST_OPEN_DEVICE_FAILED  3
#define XIL_COMPONENT_IS_READY  1
#endif

/************************** Function Prototypes *****************************/
#ifndef __linux__
#ifdef SDT
int XEye_feature_Initialize(XEye_feature *InstancePtr, UINTPTR BaseAddress);
XEye_feature_Config* XEye_feature_LookupConfig(UINTPTR BaseAddress);
#else
int XEye_feature_Initialize(XEye_feature *InstancePtr, u16 DeviceId);
XEye_feature_Config* XEye_feature_LookupConfig(u16 DeviceId);
#endif
int XEye_feature_CfgInitialize(XEye_feature *InstancePtr, XEye_feature_Config *ConfigPtr);
#else
int XEye_feature_Initialize(XEye_feature *InstancePtr, const char* InstanceName);
int XEye_feature_Release(XEye_feature *InstancePtr);
#endif

void XEye_feature_Start(XEye_feature *InstancePtr);
u32 XEye_feature_IsDone(XEye_feature *InstancePtr);
u32 XEye_feature_IsIdle(XEye_feature *InstancePtr);
u32 XEye_feature_IsReady(XEye_feature *InstancePtr);
void XEye_feature_EnableAutoRestart(XEye_feature *InstancePtr);
void XEye_feature_DisableAutoRestart(XEye_feature *InstancePtr);

void XEye_feature_Set_frame_width(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_frame_width(XEye_feature *InstancePtr);
void XEye_feature_Set_frame_height(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_frame_height(XEye_feature *InstancePtr);
void XEye_feature_Set_left_x(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_left_x(XEye_feature *InstancePtr);
void XEye_feature_Set_left_y(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_left_y(XEye_feature *InstancePtr);
void XEye_feature_Set_left_w(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_left_w(XEye_feature *InstancePtr);
void XEye_feature_Set_left_h(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_left_h(XEye_feature *InstancePtr);
void XEye_feature_Set_right_x(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_right_x(XEye_feature *InstancePtr);
void XEye_feature_Set_right_y(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_right_y(XEye_feature *InstancePtr);
void XEye_feature_Set_right_w(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_right_w(XEye_feature *InstancePtr);
void XEye_feature_Set_right_h(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_right_h(XEye_feature *InstancePtr);
void XEye_feature_Set_roi_valid(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_roi_valid(XEye_feature *InstancePtr);
void XEye_feature_Set_fixed_thresh(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_fixed_thresh(XEye_feature *InstancePtr);
void XEye_feature_Set_adapt_offset(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_adapt_offset(XEye_feature *InstancePtr);
void XEye_feature_Set_fixed_scale(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_fixed_scale(XEye_feature *InstancePtr);
void XEye_feature_Set_pixel_format(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_pixel_format(XEye_feature *InstancePtr);
void XEye_feature_Set_roi_version(XEye_feature *InstancePtr, u32 Data);
u32 XEye_feature_Get_roi_version(XEye_feature *InstancePtr);

void XEye_feature_InterruptGlobalEnable(XEye_feature *InstancePtr);
void XEye_feature_InterruptGlobalDisable(XEye_feature *InstancePtr);
void XEye_feature_InterruptEnable(XEye_feature *InstancePtr, u32 Mask);
void XEye_feature_InterruptDisable(XEye_feature *InstancePtr, u32 Mask);
void XEye_feature_InterruptClear(XEye_feature *InstancePtr, u32 Mask);
u32 XEye_feature_InterruptGetEnabled(XEye_feature *InstancePtr);
u32 XEye_feature_InterruptGetStatus(XEye_feature *InstancePtr);

#ifdef __cplusplus
}
#endif

#endif
