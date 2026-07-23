library verilog;
use verilog.vl_types.all;
entity three_t is
    port(
        en              : in     vl_logic;
        \in\            : in     vl_logic_vector(31 downto 0);
        \out\           : out    vl_logic_vector(31 downto 0)
    );
end three_t;
