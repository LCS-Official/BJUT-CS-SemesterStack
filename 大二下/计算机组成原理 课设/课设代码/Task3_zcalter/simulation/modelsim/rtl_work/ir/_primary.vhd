library verilog;
use verilog.vl_types.all;
entity ir is
    port(
        IRWr            : in     vl_logic;
        clk             : in     vl_logic;
        Instr           : in     vl_logic_vector(31 downto 0);
        irout           : out    vl_logic_vector(31 downto 0)
    );
end ir;
