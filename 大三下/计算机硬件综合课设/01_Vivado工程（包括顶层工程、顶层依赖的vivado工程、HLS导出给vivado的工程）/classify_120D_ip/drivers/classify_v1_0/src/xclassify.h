// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2023.2 (64-bit)
// Tool Version Limit: 2023.10
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef XCLASSIFY_H
#define XCLASSIFY_H

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
#include "xclassify_hw.h"

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
} XClassify_Config;
#endif

typedef struct {
    u64 Ctrl_BaseAddress;
    u32 IsReady;
} XClassify;

typedef u32 word_type;

/***************** Macros (Inline Functions) Definitions *********************/
#ifndef __linux__
#define XClassify_WriteReg(BaseAddress, RegOffset, Data) \
    Xil_Out32((BaseAddress) + (RegOffset), (u32)(Data))
#define XClassify_ReadReg(BaseAddress, RegOffset) \
    Xil_In32((BaseAddress) + (RegOffset))
#else
#define XClassify_WriteReg(BaseAddress, RegOffset, Data) \
    *(volatile u32*)((BaseAddress) + (RegOffset)) = (u32)(Data)
#define XClassify_ReadReg(BaseAddress, RegOffset) \
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
int XClassify_Initialize(XClassify *InstancePtr, UINTPTR BaseAddress);
XClassify_Config* XClassify_LookupConfig(UINTPTR BaseAddress);
#else
int XClassify_Initialize(XClassify *InstancePtr, u16 DeviceId);
XClassify_Config* XClassify_LookupConfig(u16 DeviceId);
#endif
int XClassify_CfgInitialize(XClassify *InstancePtr, XClassify_Config *ConfigPtr);
#else
int XClassify_Initialize(XClassify *InstancePtr, const char* InstanceName);
int XClassify_Release(XClassify *InstancePtr);
#endif

void XClassify_Start(XClassify *InstancePtr);
u32 XClassify_IsDone(XClassify *InstancePtr);
u32 XClassify_IsIdle(XClassify *InstancePtr);
u32 XClassify_IsReady(XClassify *InstancePtr);
void XClassify_EnableAutoRestart(XClassify *InstancePtr);
void XClassify_DisableAutoRestart(XClassify *InstancePtr);

void XClassify_Set_threshold_q(XClassify *InstancePtr, u32 Data);
u32 XClassify_Get_threshold_q(XClassify *InstancePtr);

void XClassify_InterruptGlobalEnable(XClassify *InstancePtr);
void XClassify_InterruptGlobalDisable(XClassify *InstancePtr);
void XClassify_InterruptEnable(XClassify *InstancePtr, u32 Mask);
void XClassify_InterruptDisable(XClassify *InstancePtr, u32 Mask);
void XClassify_InterruptClear(XClassify *InstancePtr, u32 Mask);
u32 XClassify_InterruptGetEnabled(XClassify *InstancePtr);
u32 XClassify_InterruptGetStatus(XClassify *InstancePtr);

#ifdef __cplusplus
}
#endif

#endif
