library verilog;
use verilog.vl_types.all;
entity sel_led is
    port(
        in1             : in     vl_logic_vector(3 downto 0);
        in2             : in     vl_logic_vector(3 downto 0);
        sel             : in     vl_logic_vector(2 downto 0);
        en              : in     vl_logic;
        \out\           : out    vl_logic_vector(3 downto 0)
    );
end sel_led;
