library verilog;
use verilog.vl_types.all;
entity timer is
    port(
        CLK_I           : in     vl_logic;
        RST_I           : in     vl_logic;
        ADD_I           : in     vl_logic_vector(5 downto 2);
        WE_I            : in     vl_logic;
        DAT_I           : in     vl_logic_vector(31 downto 0);
        DAT_O           : out    vl_logic_vector(31 downto 0);
        IRQ             : out    vl_logic;
        change          : in     vl_logic
    );
end timer;
