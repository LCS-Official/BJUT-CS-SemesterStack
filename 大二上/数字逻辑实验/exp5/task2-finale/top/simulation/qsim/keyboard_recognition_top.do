onerror {quit -f}
vlib work
vlog -work work keyboard_recognition_top.vo
vlog -work work keyboard_recognition_top.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.keyboard_recognition_top_vlg_vec_tst
vcd file -direction keyboard_recognition_top.msim.vcd
vcd add -internal keyboard_recognition_top_vlg_vec_tst/*
vcd add -internal keyboard_recognition_top_vlg_vec_tst/i1/*
add wave /*
run -all
