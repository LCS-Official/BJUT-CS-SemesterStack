set_property IOSTANDARD LVCMOS33 [get_ports cam_pclk_0]
set_property IOSTANDARD LVCMOS33 [get_ports {cam_data_0[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {cam_data_0[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {cam_data_0[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {cam_data_0[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {cam_data_0[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {cam_data_0[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {cam_data_0[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {cam_data_0[0]}]
set_property PACKAGE_PIN U18 [get_ports cam_pclk_0]
set_property PACKAGE_PIN Y14 [get_ports {cam_data_0[7]}]
set_property PACKAGE_PIN W16 [get_ports {cam_data_0[6]}]
set_property PACKAGE_PIN W14 [get_ports {cam_data_0[5]}]
set_property PACKAGE_PIN V16 [get_ports {cam_data_0[4]}]
set_property PACKAGE_PIN Y17 [get_ports {cam_data_0[3]}]
set_property PACKAGE_PIN W19 [get_ports {cam_data_0[2]}]
set_property PACKAGE_PIN Y16 [get_ports {cam_data_0[1]}]
set_property PACKAGE_PIN W18 [get_ports {cam_data_0[0]}]
set_property PACKAGE_PIN V12 [get_ports cam_href_0]
set_property PACKAGE_PIN T11 [get_ports cam_vsync_0]
set_property PACKAGE_PIN Y18 [get_ports ov_pwdn_0]
set_property PACKAGE_PIN Y19 [get_ports ov_reset_n_0]
set_property PACKAGE_PIN U19 [get_ports ov_xclk_0]
set_property PACKAGE_PIN T10 [get_ports sccb_sio_c_0]
set_property PACKAGE_PIN W13 [get_ports sccb_sio_d_0]
set_property IOSTANDARD LVCMOS33 [get_ports cam_href_0]
set_property IOSTANDARD LVCMOS33 [get_ports cam_vsync_0]
set_property IOSTANDARD LVCMOS33 [get_ports ov_pwdn_0]
set_property IOSTANDARD LVCMOS33 [get_ports ov_reset_n_0]
set_property IOSTANDARD LVCMOS33 [get_ports ov_xclk_0]
set_property IOSTANDARD LVCMOS33 [get_ports sccb_sio_c_0]
set_property IOSTANDARD LVCMOS33 [get_ports sccb_sio_d_0]
set_property PULLTYPE PULLUP [get_ports sccb_sio_d_0]



set_property PACKAGE_PIN U5 [get_ports led_r_0]
set_property PACKAGE_PIN V5 [get_ports led_g_0]
set_property PACKAGE_PIN V6 [get_ports tx_0]


# OV7670 pixel clock, assuming 24 MHz
create_clock -name cam_pclk -period 41.667 [get_ports cam_pclk_0]

# cam_pclk is asynchronous to PS generated PL clocks
set_clock_groups -asynchronous \
  -group [get_clocks cam_pclk] \
  -group [get_clocks clk_fpga_0]

set_clock_groups -asynchronous \
  -group [get_clocks cam_pclk] \
  -group [get_clocks clk_fpga_1]

set_clock_groups -asynchronous \
  -group [get_clocks cam_pclk] \
  -group [get_clocks clk_fpga_2]