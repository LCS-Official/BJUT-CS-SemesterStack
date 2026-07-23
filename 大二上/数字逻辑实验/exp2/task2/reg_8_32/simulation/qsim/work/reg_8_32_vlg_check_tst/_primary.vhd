library verilog;
use verilog.vl_types.all;
entity reg_8_32_vlg_check_tst is
    port(
        r_data          : in     vl_logic_vector(31 downto 0);
        sampler_rx      : in     vl_logic
    );
end reg_8_32_vlg_check_tst;
