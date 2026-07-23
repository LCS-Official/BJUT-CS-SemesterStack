library verilog;
use verilog.vl_types.all;
entity keyboard_recognition_top_vlg_check_tst is
    port(
        keyboard_flag   : in     vl_logic;
        keyboard_swr    : in     vl_logic_vector(3 downto 0);
        LED_out         : in     vl_logic_vector(6 downto 0);
        LED_sel         : in     vl_logic;
        sampler_rx      : in     vl_logic
    );
end keyboard_recognition_top_vlg_check_tst;
