onerror {quit -f}
vlib work
vlog -work work counter_74LS163_FINALE.vo
vlog -work work counter_74LS163_FINALE.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.counter_74LS163_FINALE_vlg_vec_tst
vcd file -direction counter_74LS163_FINALE.msim.vcd
vcd add -internal counter_74LS163_FINALE_vlg_vec_tst/*
vcd add -internal counter_74LS163_FINALE_vlg_vec_tst/i1/*
add wave /*
run -all
