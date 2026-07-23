onerror {quit -f}
vlib work
vlog -work work top_level.vo
vlog -work work top_level.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.top_level_vlg_vec_tst
vcd file -direction top_level.msim.vcd
vcd add -internal top_level_vlg_vec_tst/*
vcd add -internal top_level_vlg_vec_tst/i1/*
add wave /*
run -all
