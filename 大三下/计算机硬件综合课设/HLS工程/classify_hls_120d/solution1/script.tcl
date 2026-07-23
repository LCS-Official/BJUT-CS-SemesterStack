############################################################
## This file is generated automatically by Vitis HLS.
## Please DO NOT edit it.
## Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
## Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
############################################################
open_project classify_hls_120d
set_top classify
add_files classify_hls_120d/code/practical_svm_weights_eyefeature_binary.h
add_files classify_hls_120d/code/classify.cpp
add_files -tb classify_hls_120d/code/tb_classify.cpp -cflags "-Wno-unknown-pragmas"
open_solution "solution1" -flow_target vivado
set_part {xc7z020-clg400-1}
create_clock -period 20 -name default
config_export -format ip_catalog -output C:/Users/LC/Desktop/HardWare_CD/HLS_exports/classify_120d -rtl verilog
source "./classify_hls_120d/solution1/directives.tcl"
csim_design
csynth_design
cosim_design
export_design -rtl verilog -format ip_catalog -output C:/Users/LC/Desktop/HardWare_CD/HLS_exports/classify_120d
