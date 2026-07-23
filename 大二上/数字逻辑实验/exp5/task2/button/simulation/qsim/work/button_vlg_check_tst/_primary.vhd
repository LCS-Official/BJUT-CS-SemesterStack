library verilog;
use verilog.vl_types.all;
entity button_vlg_check_tst is
    port(
        key             : in     vl_logic_vector(3 downto 0);
        swr0            : in     vl_logic;
        swr1            : in     vl_logic;
        swr2            : in     vl_logic;
        swr3            : in     vl_logic;
        sampler_rx      : in     vl_logic
    );
end button_vlg_check_tst;
