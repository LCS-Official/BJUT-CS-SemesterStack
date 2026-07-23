transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mux_1.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mux_2.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mux_3.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mux_4.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/controller.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/outputDEV.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mips.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/PC.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/NPC.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/ALU.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/ALUOUT.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/AR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/BR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/EXT.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/IR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/GPR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/DR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/DM.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/CP0.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/Bridge.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/Timer.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/IM.v}

vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/ALU.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/ALUOUT.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/AR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/BR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/Bridge.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/controller.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mux_1.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mips_tb.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mips.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/IR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/IM.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/GPR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/EXT.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/DM.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/DR.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/CP0.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/CP.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mux_2.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mux_3.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/mux_4.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/NPC.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/outputDEV.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/registerD.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/PC.v}
vlog -vlog01compat -work work +incdir+C:/Users/LC/Desktop/LCState_pjks/Task3 {C:/Users/LC/Desktop/LCState_pjks/Task3/Timer.v}

vsim -t 1ps -L altera_ver -L lpm_ver -L sgate_ver -L altera_mf_ver -L altera_lnsim_ver -L cycloneiii_ver -L rtl_work -L work -voptargs="+acc"  mips_tb

add wave *
view structure
view signals
run -all
