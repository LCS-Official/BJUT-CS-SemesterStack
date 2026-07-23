library verilog;
use verilog.vl_types.all;
entity scanner is
    port(
        clk             : in     vl_logic;
        I_ROW           : out    vl_logic_vector(15 downto 0);
        I_COL           : out    vl_logic_vector(3 downto 0)
    );
end scanner;
