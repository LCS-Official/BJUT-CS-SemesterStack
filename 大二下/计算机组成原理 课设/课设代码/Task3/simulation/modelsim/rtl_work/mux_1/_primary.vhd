library verilog;
use verilog.vl_types.all;
entity mux_1 is
    port(
        gprsel          : in     vl_logic_vector(1 downto 0);
        rt              : in     vl_logic_vector(4 downto 0);
        rd              : in     vl_logic_vector(4 downto 0);
        m1out           : out    vl_logic_vector(4 downto 0)
    );
end mux_1;
