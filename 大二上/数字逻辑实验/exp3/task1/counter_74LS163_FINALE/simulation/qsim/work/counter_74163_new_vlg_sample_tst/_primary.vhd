library verilog;
use verilog.vl_types.all;
entity counter_74163_new_vlg_sample_tst is
    port(
        Q_in            : in     vl_logic_vector(3 downto 0);
        clk             : in     vl_logic;
        clrn            : in     vl_logic;
        enp             : in     vl_logic;
        ent             : in     vl_logic;
        ldn             : in     vl_logic;
        n_en            : in     vl_logic;
        sampler_tx      : out    vl_logic
    );
end counter_74163_new_vlg_sample_tst;
