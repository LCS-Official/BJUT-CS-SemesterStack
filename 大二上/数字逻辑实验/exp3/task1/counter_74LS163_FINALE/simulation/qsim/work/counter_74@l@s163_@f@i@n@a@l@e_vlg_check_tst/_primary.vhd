library verilog;
use verilog.vl_types.all;
entity counter_74LS163_FINALE_vlg_check_tst is
    port(
        LED_out         : in     vl_logic_vector(6 downto 0);
        rco             : in     vl_logic;
        sel             : in     vl_logic;
        sampler_rx      : in     vl_logic
    );
end counter_74LS163_FINALE_vlg_check_tst;
