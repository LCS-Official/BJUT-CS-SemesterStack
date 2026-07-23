library verilog;
use verilog.vl_types.all;
entity mux8_1_vlg_sample_tst is
    port(
        in1             : in     vl_logic_vector(31 downto 0);
        in2             : in     vl_logic_vector(31 downto 0);
        in3             : in     vl_logic_vector(31 downto 0);
        in4             : in     vl_logic_vector(31 downto 0);
        in5             : in     vl_logic_vector(31 downto 0);
        in6             : in     vl_logic_vector(31 downto 0);
        in7             : in     vl_logic_vector(31 downto 0);
        in8             : in     vl_logic_vector(31 downto 0);
        sel             : in     vl_logic_vector(2 downto 0);
        sampler_tx      : out    vl_logic
    );
end mux8_1_vlg_sample_tst;
