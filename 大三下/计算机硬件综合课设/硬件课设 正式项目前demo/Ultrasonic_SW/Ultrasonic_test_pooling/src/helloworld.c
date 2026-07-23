/******************************************************************************
* Copyright (C) 2023 Advanced Micro Devices, Inc. All Rights Reserved.
* SPDX-License-Identifier: MIT
******************************************************************************/
/*
 * helloworld.c: simple test application
 *
 * This application configures UART 16550 to baud rate 9600.
 * PS7 UART (Zynq) is not initialized by this application, since
 * bootrom/bsp configures it to baud rate 115200
 *
 * ------------------------------------------------
 * | UART TYPE   BAUD RATE                        |
 * ------------------------------------------------
 *   uartns550   9600
 *   uartlite    Configurable only in HW design
 *   ps7_uart    115200 (configured by bootrom/bsp)
 */

#include <stdio.h>
#include "platform.h"
#include "xil_printf.h"
#include "..\..\platform\hw\sdt\drivers\myUltrasonic_v1_0\src\myUltrasonic.h"
#include "xparameters.h"
#include "xil_io.h"
#include "sleep.h"

int main()
{
    int distance;

    init_platform();

    print("Hello World\n\r");
    print("Successfully ran Hello World application");

    MYULTRASONIC_mWriteReg(XPAR_MYULTRASONIC_0_BASEADDR, MYULTRASONIC_S00_AXI_SLV_REG0_OFFSET, 0x1);

    while(1)
    {
        if((MYULTRASONIC_mReadReg(XPAR_MYULTRASONIC_0_BASEADDR, MYULTRASONIC_S00_AXI_SLV_REG1_OFFSET) & 0x3) == 0x1)
        {
            distance = MYULTRASONIC_mReadReg(XPAR_MYULTRASONIC_0_BASEADDR, MYULTRASONIC_S00_AXI_SLV_REG2_OFFSET);
            printf("Distance = %.3f cm \r\n", (float)distance/10000);
        }
    }

    cleanup_platform();
    return 0;
}