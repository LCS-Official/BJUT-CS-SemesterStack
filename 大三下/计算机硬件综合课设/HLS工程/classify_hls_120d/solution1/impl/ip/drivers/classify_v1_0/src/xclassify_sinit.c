// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2023.2 (64-bit)
// Tool Version Limit: 2023.10
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef __linux__

#include "xstatus.h"
#ifdef SDT
#include "xparameters.h"
#endif
#include "xclassify.h"

extern XClassify_Config XClassify_ConfigTable[];

#ifdef SDT
XClassify_Config *XClassify_LookupConfig(UINTPTR BaseAddress) {
	XClassify_Config *ConfigPtr = NULL;

	int Index;

	for (Index = (u32)0x0; XClassify_ConfigTable[Index].Name != NULL; Index++) {
		if (!BaseAddress || XClassify_ConfigTable[Index].Ctrl_BaseAddress == BaseAddress) {
			ConfigPtr = &XClassify_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XClassify_Initialize(XClassify *InstancePtr, UINTPTR BaseAddress) {
	XClassify_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XClassify_LookupConfig(BaseAddress);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XClassify_CfgInitialize(InstancePtr, ConfigPtr);
}
#else
XClassify_Config *XClassify_LookupConfig(u16 DeviceId) {
	XClassify_Config *ConfigPtr = NULL;

	int Index;

	for (Index = 0; Index < XPAR_XCLASSIFY_NUM_INSTANCES; Index++) {
		if (XClassify_ConfigTable[Index].DeviceId == DeviceId) {
			ConfigPtr = &XClassify_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XClassify_Initialize(XClassify *InstancePtr, u16 DeviceId) {
	XClassify_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XClassify_LookupConfig(DeviceId);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XClassify_CfgInitialize(InstancePtr, ConfigPtr);
}
#endif

#endif

