library verilog;
use verilog.vl_types.all;
entity mips is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        dev1_rd         : in     vl_logic_vector(31 downto 0);
        Data2out        : out    vl_logic_vector(31 downto 0);
        IntReq          : out    vl_logic;
        cnt             : out    vl_logic_vector(31 downto 0)
    );
end mips;
