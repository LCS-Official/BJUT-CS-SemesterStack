library verilog;
use verilog.vl_types.all;
entity keyboard_recognition_vlg_check_tst is
    port(
        flag            : in     vl_logic;
        keyout          : in     vl_logic_vector(3 downto 0);
        swr             : in     vl_logic_vector(3 downto 0);
        sampler_rx      : in     vl_logic
    );
end keyboard_recognition_vlg_check_tst;
