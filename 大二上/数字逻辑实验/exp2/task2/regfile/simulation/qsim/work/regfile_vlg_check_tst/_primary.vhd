library verilog;
use verilog.vl_types.all;
entity regfile_vlg_check_tst is
    port(
        out1            : in     vl_logic_vector(31 downto 0);
        out2            : in     vl_logic_vector(31 downto 0);
        out3            : in     vl_logic_vector(31 downto 0);
        out4            : in     vl_logic_vector(31 downto 0);
        out5            : in     vl_logic_vector(31 downto 0);
        out6            : in     vl_logic_vector(31 downto 0);
        out7            : in     vl_logic_vector(31 downto 0);
        out8            : in     vl_logic_vector(31 downto 0);
        sampler_rx      : in     vl_logic
    );
end regfile_vlg_check_tst;
