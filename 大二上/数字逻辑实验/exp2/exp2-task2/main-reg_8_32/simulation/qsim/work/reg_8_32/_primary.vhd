library verilog;
use verilog.vl_types.all;
entity reg_8_32 is
    port(
        r_data          : out    vl_logic_vector(31 downto 0);
        w_r             : in     vl_logic;
        clk             : in     vl_logic;
        reset           : in     vl_logic;
        w_addr          : in     vl_logic_vector(2 downto 0);
        w_data          : in     vl_logic_vector(31 downto 0)
    );
end reg_8_32;
