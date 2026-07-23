library verilog;
use verilog.vl_types.all;
entity mux_4 is
    port(
        DR_out          : in     vl_logic_vector(31 downto 0);
        prrd            : in     vl_logic_vector(31 downto 0);
        m4out           : out    vl_logic_vector(31 downto 0);
        addr            : in     vl_logic_vector(31 downto 0)
    );
end mux_4;
