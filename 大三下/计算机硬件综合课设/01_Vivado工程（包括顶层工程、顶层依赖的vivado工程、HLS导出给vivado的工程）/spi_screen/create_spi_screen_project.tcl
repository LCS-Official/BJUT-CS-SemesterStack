set script_dir [file normalize [file dirname [info script]]]
set project_name spi_screen
set part_name xc7z020clg400-1
set project_dir [file join $script_dir vivado]
set ip_repo_dir [file join $script_dir ip_repo]
set rtl_file [file join $script_dir rtl oled_spi_lite_v1_0.v]
set ip_root [file join $ip_repo_dir oled_spi_lite_1_0]

file mkdir $project_dir
file mkdir $ip_repo_dir

create_project $project_name $project_dir -part $part_name -force
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]

add_files -norecurse $rtl_file
set_property top oled_spi_lite_v1_0 [current_fileset]
update_compile_order -fileset sources_1

puts "INFO: elaborating RTL for syntax check"
synth_design -rtl -top oled_spi_lite_v1_0 -part $part_name
close_design

if {[file exists $ip_root]} {
    file delete -force $ip_root
}

ipx::package_project \
    -root_dir $ip_root \
    -vendor lc.local \
    -library user \
    -taxonomy /UserIP \
    -import_files

set core [ipx::current_core]
set_property name oled_spi_lite $core
set_property display_name {OLED SPI Lite AXI4-Lite} $core
set_property description {AXI4-Lite controlled one-way SPI byte shifter for 128x64 OLED modules with CS/DC/RES/SDA/SCL pins.} $core
set_property version 1.0 $core
set_property vendor_display_name {LC} $core
set_property company_url {http://lc.local} $core

ipx::update_checksums $core
ipx::check_integrity $core
ipx::save_core $core

set_property ip_repo_paths $ip_repo_dir [current_project]
update_ip_catalog

puts "INFO: Vivado project created at $project_dir"
puts "INFO: Packaged IP repo created at $ip_root"
