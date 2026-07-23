library verilog;
use verilog.vl_types.all;
entity D_latch is
    port(
        D               : in     vl_logic;
        EN              : in     vl_logic;
        Q               : out    vl_logic
    );
end D_latch;
