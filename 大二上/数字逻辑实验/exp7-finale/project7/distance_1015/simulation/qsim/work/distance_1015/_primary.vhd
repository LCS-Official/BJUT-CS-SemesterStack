library verilog;
use verilog.vl_types.all;
entity distance_1015 is
    port(
        clk_hjq         : in     vl_logic;
        dis_in          : in     vl_logic_vector(1 downto 0);
        distance_result : out    vl_logic_vector(7 downto 0);
        fee_result      : out    vl_logic_vector(7 downto 0);
        clr_hjq         : in     vl_logic;
        back_trip       : in     vl_logic
    );
end distance_1015;
