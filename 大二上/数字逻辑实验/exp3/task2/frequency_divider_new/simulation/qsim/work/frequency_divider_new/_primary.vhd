library verilog;
use verilog.vl_types.all;
entity frequency_divider_new is
    port(
        clrn            : in     vl_logic;
        ldn             : in     vl_logic;
        enp             : in     vl_logic;
        ent             : in     vl_logic;
        Q_in            : in     vl_logic_vector(3 downto 0);
        rco             : out    vl_logic;
        sel             : out    vl_logic;
        rst             : in     vl_logic;
        clk_50mhz       : in     vl_logic;
        clk_1khz        : out    vl_logic;
        clk_100hz       : out    vl_logic;
        clk_10hz        : out    vl_logic;
        LED_out         : out    vl_logic_vector(6 downto 0)
    );
end frequency_divider_new;
