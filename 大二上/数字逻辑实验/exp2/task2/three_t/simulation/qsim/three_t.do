onerror {quit -f}
vlib work
vlog -work work three_t.vo
vlog -work work three_t.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.three_t_vlg_vec_tst
vcd file -direction three_t.msim.vcd
vcd add -internal three_t_vlg_vec_tst/*
vcd add -internal three_t_vlg_vec_tst/i1/*
add wave /*
run -all
