library verilog;
use verilog.vl_types.all;
entity scanner is
    port(
        clk             : in     vl_logic;
        ds              : out    vl_logic_vector(7 downto 0);
        sel             : out    vl_logic_vector(2 downto 0)
    );
end scanner;
