library verilog;
use verilog.vl_types.all;
entity button is
    port(
        swc             : in     vl_logic_vector(3 downto 0);
        swr0            : out    vl_logic;
        swr1            : out    vl_logic;
        swr2            : out    vl_logic;
        swr3            : out    vl_logic;
        clk             : in     vl_logic;
        key             : out    vl_logic_vector(3 downto 0)
    );
end button;
