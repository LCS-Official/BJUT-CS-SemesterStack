library verilog;
use verilog.vl_types.all;
entity distance_1015_vlg_sample_tst is
    port(
        back_trip       : in     vl_logic;
        clk_hjq         : in     vl_logic;
        clr_hjq         : in     vl_logic;
        dis_in          : in     vl_logic_vector(1 downto 0);
        sampler_tx      : out    vl_logic
    );
end distance_1015_vlg_sample_tst;
