library verilog;
use verilog.vl_types.all;
entity display_selector_1015 is
    port(
        n_en            : in     vl_logic;
        sel             : in     vl_logic_vector(2 downto 0);
        \out\           : out    vl_logic_vector(3 downto 0);
        in8             : in     vl_logic_vector(3 downto 0);
        in7             : in     vl_logic_vector(3 downto 0);
        in6             : in     vl_logic_vector(3 downto 0);
        in5             : in     vl_logic_vector(3 downto 0);
        in4             : in     vl_logic_vector(3 downto 0);
        in3             : in     vl_logic_vector(3 downto 0);
        in2             : in     vl_logic_vector(3 downto 0);
        in1             : in     vl_logic_vector(3 downto 0)
    );
end display_selector_1015;
