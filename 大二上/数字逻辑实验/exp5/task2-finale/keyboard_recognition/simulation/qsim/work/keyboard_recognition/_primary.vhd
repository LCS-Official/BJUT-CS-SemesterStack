library verilog;
use verilog.vl_types.all;
entity keyboard_recognition is
    port(
        swc             : in     vl_logic_vector(3 downto 0);
        swr             : out    vl_logic_vector(3 downto 0);
        clk             : in     vl_logic;
        reset           : in     vl_logic;
        flag            : out    vl_logic;
        keyout          : out    vl_logic_vector(3 downto 0)
    );
end keyboard_recognition;
