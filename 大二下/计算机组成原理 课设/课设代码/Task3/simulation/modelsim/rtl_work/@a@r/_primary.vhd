library verilog;
use verilog.vl_types.all;
entity AR is
    port(
        clk             : in     vl_logic;
        ar_in           : in     vl_logic_vector(31 downto 0);
        ar_out          : out    vl_logic_vector(31 downto 0)
    );
end AR;
