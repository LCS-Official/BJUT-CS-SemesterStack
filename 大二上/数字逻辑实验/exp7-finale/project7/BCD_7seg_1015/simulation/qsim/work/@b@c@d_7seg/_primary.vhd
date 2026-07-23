library verilog;
use verilog.vl_types.all;
entity BCD_7seg is
    port(
        n_en            : in     vl_logic;
        LED_in          : in     vl_logic_vector(3 downto 0);
        LED_out         : out    vl_logic_vector(6 downto 0);
        sel             : out    vl_logic
    );
end BCD_7seg;
