library verilog;
use verilog.vl_types.all;
entity reg_32 is
    port(
        clk             : in     vl_logic;
        rst_n           : in     vl_logic;
        \in\            : in     vl_logic_vector(31 downto 0);
        load            : in     vl_logic;
        \out\           : out    vl_logic_vector(31 downto 0)
    );
end reg_32;
