onerror {quit -f}
vlib work
vlog -work work num_led_23071005.vo
vlog -work work exp1-t1.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.num_led_23071005_vlg_vec_tst
vcd file -direction exp1-t1.msim.vcd
vcd add -internal num_led_23071005_vlg_vec_tst/*
vcd add -internal num_led_23071005_vlg_vec_tst/i1/*
add wave /*
run -all
