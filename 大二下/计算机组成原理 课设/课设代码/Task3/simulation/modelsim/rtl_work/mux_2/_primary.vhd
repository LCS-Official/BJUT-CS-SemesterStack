library verilog;
use verilog.vl_types.all;
entity mux_2 is
    port(
        WD_sel          : in     vl_logic_vector(2 downto 0);
        aluo            : in     vl_logic_vector(31 downto 0);
        DM_out          : in     vl_logic_vector(31 downto 0);
        pc_4            : in     vl_logic_vector(31 downto 0);
        m2out           : out    vl_logic_vector(31 downto 0);
        cp0out          : in     vl_logic_vector(31 downto 0)
    );
end mux_2;
