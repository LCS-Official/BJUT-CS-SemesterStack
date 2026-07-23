library verilog;
use verilog.vl_types.all;
entity sel_wd_dmin is
    port(
        addr            : in     vl_logic_vector(31 downto 0);
        dev_out         : in     vl_logic_vector(31 downto 0);
        drout           : in     vl_logic_vector(31 downto 0);
        dmin            : out    vl_logic_vector(31 downto 0)
    );
end sel_wd_dmin;
