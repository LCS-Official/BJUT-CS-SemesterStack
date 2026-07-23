library verilog;
use verilog.vl_types.all;
entity sel_gpr_datain is
    port(
        sel_gpr_datain  : in     vl_logic_vector(2 downto 0);
        aluout          : in     vl_logic_vector(31 downto 0);
        dmout           : in     vl_logic_vector(31 downto 0);
        pc_4            : in     vl_logic_vector(31 downto 0);
        gpr_datain      : out    vl_logic_vector(31 downto 0);
        cp0out          : in     vl_logic_vector(31 downto 0)
    );
end sel_gpr_datain;
