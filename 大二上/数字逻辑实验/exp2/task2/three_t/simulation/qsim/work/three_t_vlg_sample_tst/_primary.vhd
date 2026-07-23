library verilog;
use verilog.vl_types.all;
entity three_t_vlg_sample_tst is
    port(
        en              : in     vl_logic;
        \in\            : in     vl_logic_vector(31 downto 0);
        sampler_tx      : out    vl_logic
    );
end three_t_vlg_sample_tst;
