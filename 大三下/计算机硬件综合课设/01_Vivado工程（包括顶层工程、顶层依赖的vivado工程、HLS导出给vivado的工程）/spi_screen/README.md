# spi_screen / oled_spi_lite

This Vivado project packages a small AXI4-Lite IP for a 128x64 SPI OLED module.

## OLED Wiring

OLED module pins:

- `CS`  -> `oled_cs_n`
- `DC`  -> `oled_dc`
- `RES` -> `oled_res_n`
- `SDA` -> `oled_sda` / MOSI
- `SCL` -> `oled_scl` / SCLK
- `VCC` -> 3.3V supply
- `GND` -> GND

The photoed board is marked `2.42' 12864OLED 7P SPI/IIC`; the populated `R17` option indicates SPI mode.

## AXI Registers

Base offset from the IP AXI-Lite address:

- `0x00 CTRL`
  - bit0: `START` pulse, write `1` to transmit `TXDATA[7:0]`
  - bit1: `DC`, `0=command`, `1=data`
  - bit2: `CS_N`
  - bit3: `RES_N`
- `0x04 TXDATA`
  - bits `[7:0]`: byte to transmit
- `0x08 CLKDIV`
  - SPI half-period divider in AXI clock cycles; default `5`, about 10 MHz at 100 MHz AXI clock
- `0x0C STATUS`
  - bit0: busy
  - bit1: done toggle

## Build

From a Windows shell:

```powershell
D:\Xilinx\Vivado\2023.2\bin\vivado.bat -mode batch -source C:\Users\LC\Desktop\HardWare_CD\spi_screen\create_spi_screen_project.tcl
```

Generated outputs:

- Vivado project: `C:\Users\LC\Desktop\HardWare_CD\spi_screen\vivado\spi_screen.xpr`
- IP repo: `C:\Users\LC\Desktop\HardWare_CD\spi_screen\ip_repo`
- Packaged IP root: `C:\Users\LC\Desktop\HardWare_CD\spi_screen\ip_repo\oled_spi_lite_1_0`

## Use In The Main Block Design

1. Add `spi_screen/ip_repo` to the main Vivado project's IP repository paths.
2. Add `OLED SPI Lite AXI4-Lite` to the block design.
3. Connect `s00_axi_*` to the existing AXI control interconnect.
4. Connect `s00_axi_aclk` to the PS FCLK clock and reset to the matching active-low reset.
5. Make `oled_cs_n/oled_dc/oled_res_n/oled_sda/oled_scl` external and constrain them to the free pins you choose.
6. Assign an AXI address, then regenerate bitstream and hwh.

## PYNQ Driver

The standalone test XDC currently avoids the already occupied PMODA/PMODB camera pins and maps the OLED to:

- `CS`  -> `ARL00 / T14`
- `DC`  -> `ARL01 / U12`
- `RES` -> `ARL02 / U13`
- `SDA` -> `ARL03 / V13`
- `SCL` -> `ARL04 / V15`

Copy or import `python/pynq_oled_spi_lite.py` on the board. After integrating the IP:

```python
from pynq import Overlay
from pynq_oled_spi_lite import OledSpiLite, get_ip

ol = Overlay("/home/xilinx/LC_SVM/final.bit")
oled = OledSpiLite(get_ip(ol, "oled_spi_lite_0"), controller="ssd1309")
oled.init_display()
oled.show_status(frame=123, fps=7.2, alert=True, score=336022, ratio=0.82, pred=1, roi=1, eye=1, svm=1)
```

If the screen initializes but columns are shifted or blank, try `controller="sh1106"` or `controller="ssd1306"`.
