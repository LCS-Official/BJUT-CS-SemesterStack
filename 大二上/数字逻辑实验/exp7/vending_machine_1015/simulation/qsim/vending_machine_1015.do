onerror {quit -f}
vlib work
vlog -work work top.vo
vlog -work work vending_machine_1015.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.vending_machine_1015_vlg_vec_tst
vcd file -direction vending_machine_1015.msim.vcd
vcd add -internal vending_machine_1015_vlg_vec_tst/*
vcd add -internal vending_machine_1015_vlg_vec_tst/i1/*
add wave /*
run -all
