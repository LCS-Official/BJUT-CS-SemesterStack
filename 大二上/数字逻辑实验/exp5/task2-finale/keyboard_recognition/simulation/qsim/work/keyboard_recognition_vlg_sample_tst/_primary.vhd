library verilog;
use verilog.vl_types.all;
entity keyboard_recognition_vlg_sample_tst is
    port(
        clk             : in     vl_logic;
        reset           : in     vl_logic;
        swc             : in     vl_logic_vector(3 downto 0);
        sampler_tx      : out    vl_logic
    );
end keyboard_recognition_vlg_sample_tst;
