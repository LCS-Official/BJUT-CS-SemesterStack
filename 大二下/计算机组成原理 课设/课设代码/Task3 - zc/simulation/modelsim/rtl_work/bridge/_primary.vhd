library verilog;
use verilog.vl_types.all;
entity bridge is
    port(
        praddr          : in     vl_logic_vector(31 downto 0);
        bridgedin       : in     vl_logic_vector(31 downto 0);
        cpu_rd          : out    vl_logic_vector(31 downto 0);
        dev0_rd         : in     vl_logic_vector(31 downto 0);
        dev1_rd         : in     vl_logic_vector(31 downto 0);
        dev2_rd         : in     vl_logic_vector(31 downto 0);
        dev_wd          : out    vl_logic_vector(31 downto 0);
        dev_addr        : out    vl_logic_vector(3 downto 0);
        devwr           : in     vl_logic;
        dev0_we         : out    vl_logic;
        dev2_we         : out    vl_logic;
        hwint           : out    vl_logic_vector(5 downto 0);
        irq             : in     vl_logic;
        change          : out    vl_logic;
        chan            : in     vl_logic
    );
end bridge;
