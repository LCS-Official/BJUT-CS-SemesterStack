library verilog;
use verilog.vl_types.all;
entity gpr is
    port(
        clk             : in     vl_logic;
        reset           : in     vl_logic;
        regwrite        : in     vl_logic;
        gpr_rd          : in     vl_logic_vector(4 downto 0);
        gpr_datain      : in     vl_logic_vector(31 downto 0);
        rs              : in     vl_logic_vector(4 downto 0);
        rt              : in     vl_logic_vector(4 downto 0);
        busa            : out    vl_logic_vector(31 downto 0);
        busb            : out    vl_logic_vector(31 downto 0);
        overflow        : in     vl_logic
    );
end gpr;
