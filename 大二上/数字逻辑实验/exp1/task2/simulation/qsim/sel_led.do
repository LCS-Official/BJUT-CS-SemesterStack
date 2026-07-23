onerror {quit -f}
vlib work
vlog -work work sel_led.vo
vlog -work work sel_led.vt
vsim -novopt -c -t 1ps -L cycloneiii_ver -L altera_ver -L altera_mf_ver -L 220model_ver -L sgate work.sel_led_vlg_vec_tst
vcd file -direction sel_led.msim.vcd
vcd add -internal sel_led_vlg_vec_tst/*
vcd add -internal sel_led_vlg_vec_tst/i1/*
add wave /*
run -all
