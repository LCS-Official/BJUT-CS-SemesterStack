library verilog;
use verilog.vl_types.all;
entity scanner_16x16_1015 is
    port(
        buy             : in     vl_logic;
        clk_1hz         : in     vl_logic;
        insufficient    : in     vl_logic;
        n_en            : in     vl_logic;
        clk_1khz_hjq    : in     vl_logic;
        dis_in          : in     vl_logic_vector(7 downto 0);
        I_ROW           : out    vl_logic_vector(15 downto 0);
        I_COL           : out    vl_logic_vector(3 downto 0);
        bought          : out    vl_logic;
        clr_hjq         : out    vl_logic
    );
end scanner_16x16_1015;
