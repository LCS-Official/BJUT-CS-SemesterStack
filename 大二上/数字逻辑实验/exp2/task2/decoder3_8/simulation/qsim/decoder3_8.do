onerror {quit -f}
vlib work
vlog -work work decoder3_8.vo
vlog -work work decoder3_8.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.decoder3_8_vlg_vec_tst
vcd file -direction decoder3_8.msim.vcd
vcd add -internal decoder3_8_vlg_vec_tst/*
vcd add -internal decoder3_8_vlg_vec_tst/i1/*
add wave /*
run -all
