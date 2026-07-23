set script_dir [file normalize [file dirname [info script]]]
set project_xpr [file join $script_dir oled_test_vivado spi_screen_oled_test.xpr]
set out_dir [file join $script_dir outputs oled_test]

open_project $project_xpr
update_compile_order -fileset sources_1

set synth_status [get_property STATUS [get_runs synth_1]]
if {![string match "*Complete*" $synth_status]} {
    reset_run synth_1
    launch_runs synth_1 -jobs 4
    wait_on_run synth_1
    set synth_status [get_property STATUS [get_runs synth_1]]
}
if {![string match "*Complete*" $synth_status]} {
    error "synth_1 status: $synth_status"
}

set impl_status [get_property STATUS [get_runs impl_1]]
set bit_candidates [glob -nocomplain [file join $script_dir oled_test_vivado spi_screen_oled_test.runs impl_1 *.bit]]
if {![string match "*Complete*" $impl_status] || [llength $bit_candidates] == 0} {
    reset_run impl_1
    launch_runs impl_1 -to_step write_bitstream -jobs 4
    wait_on_run impl_1
    set impl_status [get_property STATUS [get_runs impl_1]]
    set bit_candidates [glob -nocomplain [file join $script_dir oled_test_vivado spi_screen_oled_test.runs impl_1 *.bit]]
}
if {![string match "*Complete*" $impl_status]} {
    error "impl_1 status: $impl_status"
}

file mkdir $out_dir
if {[llength $bit_candidates] == 0} {
    error "No bitstream found"
}
set bit_file [lindex $bit_candidates 0]
file copy -force $bit_file [file join $out_dir oled_test.bit]

set hwh_file [file join $script_dir oled_test_vivado spi_screen_oled_test.gen sources_1 bd oled_test_bd hw_handoff oled_test_bd.hwh]
if {[file exists $hwh_file]} {
    file copy -force $hwh_file [file join $out_dir oled_test.hwh]
} else {
    puts "WARNING: HWH not found at $hwh_file"
}

puts "INFO: OLED test bit copied to [file join $out_dir oled_test.bit]"
puts "INFO: OLED test hwh copied to [file join $out_dir oled_test.hwh]"
