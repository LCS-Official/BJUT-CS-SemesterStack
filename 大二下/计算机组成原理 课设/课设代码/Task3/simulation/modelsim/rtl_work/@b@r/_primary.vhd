library verilog;
use verilog.vl_types.all;
entity BR is
    port(
        clk             : in     vl_logic;
        br_in           : in     vl_logic_vector(31 downto 0);
        br_out          : out    vl_logic_vector(31 downto 0)
    );
end BR;
