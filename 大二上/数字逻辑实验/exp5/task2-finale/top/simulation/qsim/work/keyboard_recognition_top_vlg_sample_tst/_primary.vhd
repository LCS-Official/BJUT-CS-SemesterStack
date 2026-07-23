library verilog;
use verilog.vl_types.all;
entity keyboard_recognition_top_vlg_sample_tst is
    port(
        clk_50mhz       : in     vl_logic;
        frequency_n_rst : in     vl_logic;
        keyboard_rst    : in     vl_logic;
        keyboard_swc    : in     vl_logic_vector(3 downto 0);
        LED_n_en        : in     vl_logic;
        sampler_tx      : out    vl_logic
    );
end keyboard_recognition_top_vlg_sample_tst;
