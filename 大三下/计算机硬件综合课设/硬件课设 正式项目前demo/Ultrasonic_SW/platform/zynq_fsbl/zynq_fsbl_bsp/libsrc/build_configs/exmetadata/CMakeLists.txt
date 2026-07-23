
cmake_minimum_required(VERSION 3.15)
project(bsp)
        
set(DRIVER_TARGETS coresightps_dcc;devcfg;dmaps;scugic;scutimer;scuwdt;sdps;uartps;xadcps)
set(DRIVER_LOCATIONS D:/Xilinx/Vitis/2023.2/data/embeddedsw/XilinxProcessorIPLib/drivers/coresightps_dcc_v1_9;D:/Xilinx/Vitis/2023.2/data/embeddedsw/XilinxProcessorIPLib/drivers/devcfg_v3_8;D:/Xilinx/Vitis/2023.2/data/embeddedsw/XilinxProcessorIPLib/drivers/dmaps_v2_9;D:/Xilinx/Vitis/2023.2/data/embeddedsw/XilinxProcessorIPLib/drivers/scugic_v5_2;D:/Xilinx/Vitis/2023.2/data/embeddedsw/XilinxProcessorIPLib/drivers/scutimer_v2_5;D:/Xilinx/Vitis/2023.2/data/embeddedsw/XilinxProcessorIPLib/drivers/scuwdt_v2_5;D:/Xilinx/Vitis/2023.2/data/embeddedsw/XilinxProcessorIPLib/drivers/sdps_v4_2;D:/Xilinx/Vitis/2023.2/data/embeddedsw/XilinxProcessorIPLib/drivers/uartps_v3_13;D:/Xilinx/Vitis/2023.2/data/embeddedsw/XilinxProcessorIPLib/drivers/xadcps_v2_7)

list(LENGTH DRIVER_TARGETS no_of_drivers)
set(index 0)

while(${index} LESS ${no_of_drivers})
    list(GET DRIVER_TARGETS ${index} drv)
    list(GET DRIVER_LOCATIONS ${index} drv_dir)
    set(exp_dir "${drv_dir}/examples")
    add_custom_target(
        ${drv}_example ALL
        COMMAND lopper -f -O C:/Users/LC/Desktop/HardwareCourseDesign/Ultrasonic_SW/platform/zynq_fsbl/zynq_fsbl_bsp/libsrc/${drv} C:/Users/LC/Desktop/HardwareCourseDesign/Ultrasonic_SW/platform/zynq_fsbl/zynq_fsbl_bsp/hw_artifacts/ps7_cortexa9_0_baremetal.dts -- bmcmake_metadata_xlnx ps7_cortexa9_0 ${exp_dir} drvcmake_metadata
        BYPRODUCTS x${drv}_exlist.yaml)
    MATH(EXPR index "${index}+1")
endwhile()
