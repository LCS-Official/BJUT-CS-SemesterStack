library verilog;
use verilog.vl_types.all;
entity DR is
    port(
        clk             : in     vl_logic;
        dr_in           : in     vl_logic_vector(31 downto 0);
        dr_out          : out    vl_logic_vector(31 downto 0)
    );
end DR;
