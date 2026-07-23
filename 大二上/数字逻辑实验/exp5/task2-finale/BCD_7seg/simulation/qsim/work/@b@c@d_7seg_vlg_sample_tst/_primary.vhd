library verilog;
use verilog.vl_types.all;
entity BCD_7seg_vlg_sample_tst is
    port(
        data            : in     vl_logic_vector(3 downto 0);
        dpin            : in     vl_logic;
        n_en            : in     vl_logic;
        sampler_tx      : out    vl_logic
    );
end BCD_7seg_vlg_sample_tst;
