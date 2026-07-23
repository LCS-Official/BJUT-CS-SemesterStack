library verilog;
use verilog.vl_types.all;
entity gpr is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        reg_write       : in     vl_logic;
        read_reg1       : in     vl_logic_vector(4 downto 0);
        read_reg2       : in     vl_logic_vector(4 downto 0);
        write_reg       : in     vl_logic_vector(4 downto 0);
        write_data      : in     vl_logic_vector(31 downto 0);
        read_data1      : out    vl_logic_vector(31 downto 0);
        read_data2      : out    vl_logic_vector(31 downto 0)
    );
end gpr;
