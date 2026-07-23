library verilog;
use verilog.vl_types.all;
entity scanner_16x16_1015_vlg_check_tst is
    port(
        I_COL           : in     vl_logic_vector(3 downto 0);
        I_ROW           : in     vl_logic_vector(15 downto 0);
        bought          : in     vl_logic;
        clr_hjq         : in     vl_logic;
        sampler_rx      : in     vl_logic
    );
end scanner_16x16_1015_vlg_check_tst;
