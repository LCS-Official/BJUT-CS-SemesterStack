onerror {quit -f}
vlib work
vlog -work work button.vo
vlog -work work button.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.button_vlg_vec_tst
vcd file -direction button.msim.vcd
vcd add -internal button_vlg_vec_tst/*
vcd add -internal button_vlg_vec_tst/i1/*
add wave /*
run -all
