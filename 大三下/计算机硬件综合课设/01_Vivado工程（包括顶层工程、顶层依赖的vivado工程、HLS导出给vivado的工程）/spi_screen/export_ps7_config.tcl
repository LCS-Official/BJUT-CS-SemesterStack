set old_project {C:/Users/LC/Desktop/HardWare_CD/7670vdmafinal/7670vdmafinal.xpr}
set old_bd {C:/Users/LC/Desktop/HardWare_CD/7670vdmafinal/7670vdmafinal.srcs/sources_1/bd/design_1/design_1.bd}
set out_tcl {C:/Users/LC/Desktop/HardWare_CD/spi_screen/ps7_config_from_7670vdmafinal.tcl}

open_project $old_project
open_bd_design $old_bd
set ps [get_bd_cells processing_system7_0]
set fd [open $out_tcl w]
puts $fd "set_property -dict \[list \\"
foreach p [lsort [list_property $ps]] {
    if {[string match {CONFIG.*} $p]} {
        if {[string match {CONFIG.PCW_ACT_*} $p]} {
            continue
        }
        if {[regexp {^CONFIG\.PCW_.*_FREQMHZ$} $p] && ![regexp {^CONFIG\.PCW_FPGA[0-3]_PERIPHERAL_FREQMHZ$} $p]} {
            continue
        }
        if {$p eq "CONFIG.PCW_NUM_F2P_INTR_INPUTS"} {
            continue
        }
        set v [get_property $p $ps]
        if {$v ne ""} {
            puts $fd "    $p {$v} \\"
        }
    }
}
puts $fd "\] \[get_bd_cells processing_system7_0\]"
close $fd
puts "INFO: wrote $out_tcl"
