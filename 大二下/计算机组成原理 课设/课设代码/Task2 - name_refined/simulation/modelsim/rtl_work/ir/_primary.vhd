library verilog;
use verilog.vl_types.all;
entity ir is
    port(
        clk             : in     vl_logic;
        ins             : in     vl_logic_vector(31 downto 0);
        rs              : out    vl_logic_vector(4 downto 0);
        rt              : out    vl_logic_vector(4 downto 0);
        rd              : out    vl_logic_vector(4 downto 0);
        func            : out    vl_logic_vector(5 downto 0);
        OpCode          : out    vl_logic_vector(5 downto 0);
        imm26           : out    vl_logic_vector(25 downto 0);
        IRWrite         : in     vl_logic
    );
end ir;
