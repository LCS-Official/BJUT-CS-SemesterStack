library verilog;
use verilog.vl_types.all;
entity reg_32_vlg_check_tst is
    port(
        \out\           : in     vl_logic_vector(31 downto 0);
        sampler_rx      : in     vl_logic
    );
end reg_32_vlg_check_tst;
