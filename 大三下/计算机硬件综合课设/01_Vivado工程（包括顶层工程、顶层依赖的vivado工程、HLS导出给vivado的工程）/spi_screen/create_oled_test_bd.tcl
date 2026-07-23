set script_dir [file normalize [file dirname [info script]]]
set project_name spi_screen_oled_test
set project_dir [file join $script_dir oled_test_vivado]
set part_name xc7z020clg400-1
set ip_repo_dir [file join $script_dir ip_repo]
set ps7_cfg [file join $script_dir ps7_config_from_7670vdmafinal.tcl]
set xdc_file [file join $script_dir constraints oled_test_ja.xdc]
set bd_name oled_test_bd

create_project $project_name $project_dir -part $part_name -force
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_property ip_repo_paths $ip_repo_dir [current_project]
update_ip_catalog

set bd_dir [file join $project_dir ${project_name}.srcs sources_1 bd $bd_name]
if {[file exists $bd_dir]} {
    file delete -force $bd_dir
}

create_bd_design $bd_name

create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0
source $ps7_cfg
set_property -dict [list \
    CONFIG.PCW_USE_M_AXI_GP0 {1} \
    CONFIG.PCW_EN_CLK0_PORT {1} \
    CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {100} \
    CONFIG.PCW_USE_S_AXI_HP0 {0} \
    CONFIG.PCW_USE_S_AXI_HP1 {0} \
    CONFIG.PCW_USE_S_AXI_HP2 {0} \
    CONFIG.PCW_USE_S_AXI_HP3 {0} \
] [get_bd_cells processing_system7_0]

make_bd_intf_pins_external [get_bd_intf_pins processing_system7_0/DDR]
make_bd_intf_pins_external [get_bd_intf_pins processing_system7_0/FIXED_IO]

create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 rst_ps7_0_100M
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 axi_interconnect_0
set_property -dict [list CONFIG.NUM_MI {1}] [get_bd_cells axi_interconnect_0]

create_bd_cell -type ip -vlnv lc.local:user:oled_spi_lite:1.0 oled_spi_lite_0

connect_bd_intf_net [get_bd_intf_pins processing_system7_0/M_AXI_GP0] [get_bd_intf_pins axi_interconnect_0/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M00_AXI] [get_bd_intf_pins oled_spi_lite_0/s00_axi]

connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] [get_bd_pins rst_ps7_0_100M/slowest_sync_clk]
connect_bd_net [get_bd_pins processing_system7_0/FCLK_RESET0_N] [get_bd_pins rst_ps7_0_100M/ext_reset_in]

connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
    [get_bd_pins processing_system7_0/M_AXI_GP0_ACLK] \
    [get_bd_pins axi_interconnect_0/ACLK] \
    [get_bd_pins axi_interconnect_0/S00_ACLK] \
    [get_bd_pins axi_interconnect_0/M00_ACLK] \
    [get_bd_pins oled_spi_lite_0/s00_axi_aclk]

connect_bd_net [get_bd_pins rst_ps7_0_100M/peripheral_aresetn] \
    [get_bd_pins axi_interconnect_0/ARESETN] \
    [get_bd_pins axi_interconnect_0/S00_ARESETN] \
    [get_bd_pins axi_interconnect_0/M00_ARESETN] \
    [get_bd_pins oled_spi_lite_0/s00_axi_aresetn]

foreach pin {oled_cs_n oled_dc oled_res_n oled_scl oled_sda} {
    create_bd_port -dir O $pin
    connect_bd_net [get_bd_pins oled_spi_lite_0/$pin] [get_bd_ports $pin]
}

assign_bd_address
foreach seg [get_bd_addr_segs -of_objects [get_bd_addr_spaces processing_system7_0/Data]] {
    if {[string match {*oled_spi_lite_0*} $seg]} {
        set_property offset 0x43C00000 $seg
        set_property range 64K $seg
    }
}

validate_bd_design
save_bd_design

set bd_file [get_files [file join $bd_dir ${bd_name}.bd]]
set wrapper [make_wrapper -files $bd_file -top]
add_files -norecurse $wrapper
set_property top ${bd_name}_wrapper [current_fileset]
update_compile_order -fileset sources_1

if {[llength [get_files -quiet $xdc_file]] == 0} {
    add_files -fileset constrs_1 -norecurse $xdc_file
}
set_property used_in_synthesis true [get_files $xdc_file]
set_property used_in_implementation true [get_files $xdc_file]

puts "INFO: created standalone OLED test BD: $bd_name"
puts "INFO: test project: [file join $project_dir ${project_name}.xpr]"
puts "INFO: default XDC uses free Arduino pins: CS=ARL00/T14 DC=ARL01/U12 RES=ARL02/U13 SDA=ARL03/V13 SCL=ARL04/V15"
