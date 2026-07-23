## Example only. Edit PACKAGE_PIN values for your chosen PYNQ-Z1 PMOD pins.
## OLED module pins: CS, DC, RES, SDA, SCL, VCC, GND.
## Use 3.3V logic. Do not connect OLED VCC to a PL I/O pin.

# set_property PACKAGE_PIN <PMOD_PIN_FOR_CS>  [get_ports oled_cs_n]
# set_property PACKAGE_PIN <PMOD_PIN_FOR_DC>  [get_ports oled_dc]
# set_property PACKAGE_PIN <PMOD_PIN_FOR_RES> [get_ports oled_res_n]
# set_property PACKAGE_PIN <PMOD_PIN_FOR_SDA> [get_ports oled_sda]
# set_property PACKAGE_PIN <PMOD_PIN_FOR_SCL> [get_ports oled_scl]

# set_property IOSTANDARD LVCMOS33 [get_ports {oled_cs_n oled_dc oled_res_n oled_sda oled_scl}]
