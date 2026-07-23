set script_dir [file normalize [file dirname [info script]]]
set proj_dir [file normalize [file join $script_dir ".."]]

open_project $proj_dir
set_top eye_feature
add_files [file join $script_dir "eye_feature.cpp"]
add_files -tb [file join $script_dir "tb_eye_feature.cpp"]
open_solution solution1 -flow_target vivado
set_part xc7z020clg400-1
create_clock -period 20 -name default
csim_design
csynth_design
export_design -flow syn -rtl verilog -format ip_catalog
