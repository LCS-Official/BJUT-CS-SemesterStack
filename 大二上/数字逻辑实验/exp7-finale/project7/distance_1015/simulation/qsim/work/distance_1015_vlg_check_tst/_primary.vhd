library verilog;
use verilog.vl_types.all;
entity distance_1015_vlg_check_tst is
    port(
        distance_result : in     vl_logic_vector(7 downto 0);
        fee_result      : in     vl_logic_vector(7 downto 0);
        sampler_rx      : in     vl_logic
    );
end distance_1015_vlg_check_tst;
