library verilog;
use verilog.vl_types.all;
entity sel_gpr_rd is
    port(
        sel_gpr_rd      : in     vl_logic_vector(1 downto 0);
        rt              : in     vl_logic_vector(4 downto 0);
        rd              : in     vl_logic_vector(4 downto 0);
        gpr_rd          : out    vl_logic_vector(4 downto 0)
    );
end sel_gpr_rd;
