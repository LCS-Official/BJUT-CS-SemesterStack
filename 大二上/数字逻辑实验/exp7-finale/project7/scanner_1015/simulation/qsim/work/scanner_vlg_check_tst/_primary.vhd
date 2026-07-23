library verilog;
use verilog.vl_types.all;
entity scanner_vlg_check_tst is
    port(
        ds              : in     vl_logic_vector(7 downto 0);
        sel             : in     vl_logic_vector(2 downto 0);
        sampler_rx      : in     vl_logic
    );
end scanner_vlg_check_tst;
