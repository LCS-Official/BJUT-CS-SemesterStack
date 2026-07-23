library verilog;
use verilog.vl_types.all;
entity BCD_7seg_vlg_check_tst is
    port(
        LED_out         : in     vl_logic_vector(6 downto 0);
        sel             : in     vl_logic;
        sampler_rx      : in     vl_logic
    );
end BCD_7seg_vlg_check_tst;
