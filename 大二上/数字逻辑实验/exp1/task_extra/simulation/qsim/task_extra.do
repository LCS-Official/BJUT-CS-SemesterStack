onerror {quit -f}
vlib work
vlog -work work combined_task_23071005.vo
vlog -work work task_extra.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.task_extra_vlg_vec_tst
vcd file -direction task_extra.msim.vcd
vcd add -internal task_extra_vlg_vec_tst/*
vcd add -internal task_extra_vlg_vec_tst/i1/*
add wave /*
run -all
