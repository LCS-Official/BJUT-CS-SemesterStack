library verilog;
use verilog.vl_types.all;
entity reg_32_vlg_sample_tst is
    port(
        clk             : in     vl_logic;
        \in\            : in     vl_logic_vector(31 downto 0);
        load            : in     vl_logic;
        rst_n           : in     vl_logic;
        sampler_tx      : out    vl_logic
    );
end reg_32_vlg_sample_tst;
