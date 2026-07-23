library verilog;
use verilog.vl_types.all;
entity output_dev is
    port(
        clk             : in     vl_logic;
        en              : in     vl_logic;
        addr            : in     vl_logic_vector(5 downto 2);
        din             : in     vl_logic_vector(31 downto 0);
        dout            : out    vl_logic_vector(31 downto 0)
    );
end output_dev;
