library verilog;
use verilog.vl_types.all;
entity output_dev is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        en              : in     vl_logic;
        addr            : in     vl_logic_vector(3 downto 0);
        din             : in     vl_logic_vector(31 downto 0);
        dout            : out    vl_logic_vector(31 downto 0)
    );
end output_dev;
