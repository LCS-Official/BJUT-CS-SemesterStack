library verilog;
use verilog.vl_types.all;
entity dm is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        we              : in     vl_logic;
        addr            : in     vl_logic_vector(9 downto 0);
        din             : in     vl_logic_vector(31 downto 0);
        dout            : out    vl_logic_vector(31 downto 0)
    );
end dm;
