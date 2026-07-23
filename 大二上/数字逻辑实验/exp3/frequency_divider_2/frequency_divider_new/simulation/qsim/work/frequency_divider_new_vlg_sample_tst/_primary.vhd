library verilog;
use verilog.vl_types.all;
entity frequency_divider_new_vlg_sample_tst is
    port(
        clk_50mhz       : in     vl_logic;
        clr_n           : in     vl_logic;
        enp             : in     vl_logic;
        ent             : in     vl_logic;
        ld_n            : in     vl_logic;
        q_in            : in     vl_logic_vector(3 downto 0);
        rst             : in     vl_logic;
        sampler_tx      : out    vl_logic
    );
end frequency_divider_new_vlg_sample_tst;
