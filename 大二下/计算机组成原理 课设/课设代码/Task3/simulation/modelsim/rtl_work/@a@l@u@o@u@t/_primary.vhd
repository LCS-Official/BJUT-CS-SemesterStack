library verilog;
use verilog.vl_types.all;
entity ALUOUT is
    port(
        clk             : in     vl_logic;
        aluout_in       : in     vl_logic_vector(31 downto 0);
        aluout_out      : out    vl_logic_vector(31 downto 0)
    );
end ALUOUT;
