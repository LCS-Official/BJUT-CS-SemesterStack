onerror {quit -f}
vlib work
vlog -work work distance_1015.vo
vlog -work work distance_1015.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.distance_1015_vlg_vec_tst
vcd file -direction distance_1015.msim.vcd
vcd add -internal distance_1015_vlg_vec_tst/*
vcd add -internal distance_1015_vlg_vec_tst/i1/*
add wave /*
run -all
