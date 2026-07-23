library verilog;
use verilog.vl_types.all;
entity BCD_7seg is
    port(
        n_en            : in     vl_logic;
        data            : in     vl_logic_vector(3 downto 0);
        dpin            : in     vl_logic;
        \out\           : out    vl_logic_vector(6 downto 0);
        dpout           : out    vl_logic;
        sel             : out    vl_logic
    );
end BCD_7seg;
