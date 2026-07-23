onerror {quit -f}
vlib work
vlog -work work regfile.vo
vlog -work work regfile.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.regfile_vlg_vec_tst
vcd file -direction regfile.msim.vcd
vcd add -internal regfile_vlg_vec_tst/*
vcd add -internal regfile_vlg_vec_tst/i1/*
add wave /*
run -all
