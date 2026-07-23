library verilog;
use verilog.vl_types.all;
entity sel_led_vlg_sample_tst is
    port(
        en              : in     vl_logic;
        in1             : in     vl_logic_vector(3 downto 0);
        in2             : in     vl_logic_vector(3 downto 0);
        sel             : in     vl_logic_vector(2 downto 0);
        sampler_tx      : out    vl_logic
    );
end sel_led_vlg_sample_tst;
