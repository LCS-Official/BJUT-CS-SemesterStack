############################################################
## This file is generated automatically by Vitis HLS.
## Please DO NOT edit it.
## Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
## Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
############################################################
open_project eyefeature_robust8
set_top eye_feature
add_files eyefeature_robust8/code/eye_feature.cpp
add_files -tb eyefeature_robust8/code/tb_eye_feature.cpp -cflags "-Wno-unknown-pragmas"
open_solution "solution1" -flow_target vivado
set_part {xc7z020-clg400-1}
create_clock -period 20 -name default
config_cosim -tool xsim
config_export -format ip_catalog -output C:/Users/LC/Desktop/HardWare_CD/HLS_exports/eyefeature_robust8 -rtl verilog -vivado_clock 20
source "./eyefeature_robust8/solution1/directives.tcl"
csim_design
csynth_design
cosim_design
export_design -rtl verilog -format ip_catalog -output C:/Users/LC/Desktop/HardWare_CD/HLS_exports/eyefeature_robust8
