library verilog;
use verilog.vl_types.all;
entity dm is
    port(
        clk             : in     vl_logic;
        mem_read        : in     vl_logic;
        mem_write       : in     vl_logic;
        addr            : in     vl_logic_vector(31 downto 0);
        write_data      : in     vl_logic_vector(31 downto 0);
        data_size       : in     vl_logic_vector(1 downto 0);
        read_data       : out    vl_logic_vector(31 downto 0)
    );
end dm;
