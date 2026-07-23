## Standalone OLED test pinout for currently free PYNQ-Z1 Arduino digital pins.
## This avoids PMODA/PMODB, which are already occupied by the OV7670 camera,
## and avoids ARH26/ARH27/ARH28, which are used by LED/TTS in the main system.
## Wire the OLED module as:
##   CS  -> ARL00 / T14
##   DC  -> ARL01 / U12
##   RES -> ARL02 / U13
##   SDA -> ARL03 / V13
##   SCL -> ARL04 / V15
##   VCC -> 3V3
##   GND -> GND

set_property PACKAGE_PIN T14 [get_ports oled_cs_n]
set_property PACKAGE_PIN U12 [get_ports oled_dc]
set_property PACKAGE_PIN U13 [get_ports oled_res_n]
set_property PACKAGE_PIN V13 [get_ports oled_sda]
set_property PACKAGE_PIN V15 [get_ports oled_scl]

set_property IOSTANDARD LVCMOS33 [get_ports {oled_cs_n oled_dc oled_res_n oled_sda oled_scl}]
