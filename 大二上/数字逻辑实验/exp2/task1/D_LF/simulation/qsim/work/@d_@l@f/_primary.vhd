library verilog;
use verilog.vl_types.all;
entity D_LF is
    port(
        Q2              : out    vl_logic;
        clk             : in     vl_logic;
        D               : in     vl_logic;
        Q1              : out    vl_logic;
        EN              : in     vl_logic
    );
end D_LF;
