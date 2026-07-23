transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vlog -vlog01compat -work work +incdir+D:/LCsexp2/exp2-task1/D_LF {D:/LCsexp2/exp2-task1/D_LF/D_latch.v}
vlog -vlog01compat -work work +incdir+D:/LCsexp2/exp2-task1/D_LF {D:/LCsexp2/exp2-task1/D_LF/D_FF.v}

