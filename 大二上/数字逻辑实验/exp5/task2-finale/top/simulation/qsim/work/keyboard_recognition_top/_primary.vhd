library verilog;
use verilog.vl_types.all;
entity keyboard_recognition_top is
    port(
        keyboard_flag   : out    vl_logic;
        clk_50mhz       : in     vl_logic;
        frequency_n_rst : in     vl_logic;
        keyboard_rst    : in     vl_logic;
        keyboard_swc    : in     vl_logic_vector(3 downto 0);
        LED_sel         : out    vl_logic;
        LED_n_en        : in     vl_logic;
        keyboard_swr    : out    vl_logic_vector(3 downto 0);
        LED_out         : out    vl_logic_vector(6 downto 0)
    );
end keyboard_recognition_top;
