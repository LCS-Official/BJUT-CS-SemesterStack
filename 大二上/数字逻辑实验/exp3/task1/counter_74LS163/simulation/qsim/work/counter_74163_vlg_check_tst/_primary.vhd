library verilog;
use verilog.vl_types.all;
entity counter_74163_vlg_check_tst is
    port(
        Q_out           : in     vl_logic_vector(3 downto 0);
        rco             : in     vl_logic;
        sampler_rx      : in     vl_logic
    );
end counter_74163_vlg_check_tst;
