library verilog;
use verilog.vl_types.all;
entity frequency_divider_1015 is
    port(
        clk_50mhz       : in     vl_logic;
        clk_100hz       : out    vl_logic
    );
end frequency_divider_1015;
