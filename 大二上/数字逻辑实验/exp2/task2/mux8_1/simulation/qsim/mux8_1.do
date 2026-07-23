onerror {quit -f}
vlib work
vlog -work work mux8_1.vo
vlog -work work mux8_1.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.mux8_1_vlg_vec_tst
vcd file -direction mux8_1.msim.vcd
vcd add -internal mux8_1_vlg_vec_tst/*
vcd add -internal mux8_1_vlg_vec_tst/i1/*
add wave /*
run -all
