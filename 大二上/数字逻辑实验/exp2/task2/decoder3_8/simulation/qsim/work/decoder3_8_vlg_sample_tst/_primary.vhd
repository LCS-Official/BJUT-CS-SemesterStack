library verilog;
use verilog.vl_types.all;
entity decoder3_8_vlg_sample_tst is
    port(
        \in\            : in     vl_logic_vector(2 downto 0);
        sampler_tx      : out    vl_logic
    );
end decoder3_8_vlg_sample_tst;
