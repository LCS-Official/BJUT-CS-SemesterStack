library verilog;
use verilog.vl_types.all;
entity PC is
    port(
        clk             : in     vl_logic;
        PC_wr           : in     vl_logic;
        pcin            : in     vl_logic_vector(31 downto 0);
        pcout           : out    vl_logic_vector(31 downto 0)
    );
end PC;
