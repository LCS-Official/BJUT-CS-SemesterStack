library verilog;
use verilog.vl_types.all;
entity reg_8_32_vlg_sample_tst is
    port(
        clk             : in     vl_logic;
        reset           : in     vl_logic;
        w_addr          : in     vl_logic_vector(2 downto 0);
        w_data          : in     vl_logic_vector(31 downto 0);
        w_r             : in     vl_logic;
        sampler_tx      : out    vl_logic
    );
end reg_8_32_vlg_sample_tst;
