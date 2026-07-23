onerror {quit -f}
vlib work
vlog -work work reg_8_32.vo
vlog -work work reg_8_32.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.reg_8_32_vlg_vec_tst
vcd file -direction reg_8_32.msim.vcd
vcd add -internal reg_8_32_vlg_vec_tst/*
vcd add -internal reg_8_32_vlg_vec_tst/i1/*
add wave /*
run -all
