transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/regb.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/regaluout.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/rega.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/PC.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/NPC.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/mips.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/IR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/GPR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/EXT.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/dm.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/Controller.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/ALU.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/im_1k.v}

vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/Controller.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/ALU.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/dm.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/EXT.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/GPR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/im_1k.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/IR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/mips.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/test_mips_tb.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/regb.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/regaluout.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/rega.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/PC.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task2 {C:/Users/LC/Desktop/LCState_pjks/Task2/NPC.v}

vsim -t 1ps -L altera_ver -L lpm_ver -L sgate_ver -L altera_mf_ver -L altera_lnsim_ver -L cycloneiv_hssi_ver -L cycloneiv_pcie_hip_ver -L cycloneiv_ver -L rtl_work -L work -voptargs="+acc"  test_mips_tb

add wave *
view structure
view signals
run -all
