library verilog;
use verilog.vl_types.all;
entity top_level_vlg_sample_tst is
    port(
        clk_50mhz       : in     vl_logic;
        in1             : in     vl_logic_vector(3 downto 0);
        in2             : in     vl_logic_vector(3 downto 0);
        n_en            : in     vl_logic;
        sampler_tx      : out    vl_logic
    );
end top_level_vlg_sample_tst;
