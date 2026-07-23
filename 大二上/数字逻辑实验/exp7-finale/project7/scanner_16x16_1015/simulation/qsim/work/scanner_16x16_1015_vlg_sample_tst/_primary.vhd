library verilog;
use verilog.vl_types.all;
entity scanner_16x16_1015_vlg_sample_tst is
    port(
        buy             : in     vl_logic;
        clk_1hz         : in     vl_logic;
        clk_1khz_hjq    : in     vl_logic;
        dis_in          : in     vl_logic_vector(7 downto 0);
        insufficient    : in     vl_logic;
        n_en            : in     vl_logic;
        sampler_tx      : out    vl_logic
    );
end scanner_16x16_1015_vlg_sample_tst;
