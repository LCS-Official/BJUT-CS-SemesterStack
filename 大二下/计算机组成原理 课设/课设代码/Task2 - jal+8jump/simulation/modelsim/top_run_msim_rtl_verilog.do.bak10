transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/defines.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/gpr.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/ext.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/dm.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/pc.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/im.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/alu.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/npc.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/datapath.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/controller.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/mips.v}

vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/alu.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/controller.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/datapath.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/defines.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/dm.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/ext.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/gpr.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/im.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/mips.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/npc.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/pc.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task1 {C:/Users/LC/Desktop/LCState_pjks/Task1/test_mips_tb.v}

vsim -t 1ps -L altera_ver -L lpm_ver -L sgate_ver -L altera_mf_ver -L altera_lnsim_ver -L cycloneiv_hssi_ver -L cycloneiv_pcie_hip_ver -L cycloneiv_ver -L rtl_work -L work -voptargs="+acc"  test_mips_tb

add wave *
view structure
view signals
run -all
