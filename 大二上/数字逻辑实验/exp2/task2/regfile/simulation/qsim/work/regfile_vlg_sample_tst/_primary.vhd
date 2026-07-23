library verilog;
use verilog.vl_types.all;
entity regfile_vlg_sample_tst is
    port(
        clk             : in     vl_logic;
        en1             : in     vl_logic;
        en2             : in     vl_logic;
        en3             : in     vl_logic;
        en4             : in     vl_logic;
        en5             : in     vl_logic;
        en6             : in     vl_logic;
        en7             : in     vl_logic;
        en8             : in     vl_logic;
        \in\            : in     vl_logic_vector(31 downto 0);
        rst_n           : in     vl_logic;
        w_r             : in     vl_logic;
        sampler_tx      : out    vl_logic
    );
end regfile_vlg_sample_tst;
