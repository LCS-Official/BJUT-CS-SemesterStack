library verilog;
use verilog.vl_types.all;
entity sel_led_vlg_check_tst is
    port(
        \out\           : in     vl_logic_vector(3 downto 0);
        sampler_rx      : in     vl_logic
    );
end sel_led_vlg_check_tst;
