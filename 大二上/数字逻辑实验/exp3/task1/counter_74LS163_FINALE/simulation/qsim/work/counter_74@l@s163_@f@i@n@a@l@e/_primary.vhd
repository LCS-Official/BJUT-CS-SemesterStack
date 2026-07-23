library verilog;
use verilog.vl_types.all;
entity counter_74LS163_FINALE is
    port(
        clrn            : in     vl_logic;
        ldn             : in     vl_logic;
        enp             : in     vl_logic;
        ent             : in     vl_logic;
        clk             : in     vl_logic;
        Q_in            : in     vl_logic_vector(3 downto 0);
        rco             : out    vl_logic;
        n_en            : in     vl_logic;
        LED_out         : out    vl_logic_vector(6 downto 0);
        sel             : out    vl_logic
    );
end counter_74LS163_FINALE;
