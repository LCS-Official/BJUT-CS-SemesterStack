library verilog;
use verilog.vl_types.all;
entity display_selector_1015_vlg_sample_tst is
    port(
        change_out      : in     vl_logic_vector(7 downto 0);
        distance_out    : in     vl_logic_vector(7 downto 0);
        fee_out         : in     vl_logic_vector(7 downto 0);
        n_en            : in     vl_logic;
        sel_hjq         : in     vl_logic_vector(2 downto 0);
        vendingmachine_out: in     vl_logic_vector(7 downto 0);
        sampler_tx      : out    vl_logic
    );
end display_selector_1015_vlg_sample_tst;
