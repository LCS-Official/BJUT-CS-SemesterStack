library verilog;
use verilog.vl_types.all;
entity top_level is
    port(
        n_en            : in     vl_logic;
        in1             : in     vl_logic_vector(3 downto 0);
        in2             : in     vl_logic_vector(3 downto 0);
        clk_50mhz       : in     vl_logic;
        ds              : out    vl_logic_vector(7 downto 0);
        led             : out    vl_logic_vector(6 downto 0)
    );
end top_level;
