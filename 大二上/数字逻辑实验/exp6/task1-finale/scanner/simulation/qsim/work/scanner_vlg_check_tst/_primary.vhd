library verilog;
use verilog.vl_types.all;
entity scanner_vlg_check_tst is
    port(
        I_COL           : in     vl_logic_vector(3 downto 0);
        I_ROW           : in     vl_logic_vector(15 downto 0);
        sampler_rx      : in     vl_logic
    );
end scanner_vlg_check_tst;
