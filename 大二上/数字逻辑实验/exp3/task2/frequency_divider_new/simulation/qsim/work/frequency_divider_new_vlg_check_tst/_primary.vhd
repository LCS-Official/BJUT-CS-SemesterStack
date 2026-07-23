library verilog;
use verilog.vl_types.all;
entity frequency_divider_new_vlg_check_tst is
    port(
        LED_out         : in     vl_logic_vector(6 downto 0);
        clk_1khz        : in     vl_logic;
        clk_10hz        : in     vl_logic;
        clk_100hz       : in     vl_logic;
        rco             : in     vl_logic;
        sel             : in     vl_logic;
        sampler_rx      : in     vl_logic
    );
end frequency_divider_new_vlg_check_tst;
