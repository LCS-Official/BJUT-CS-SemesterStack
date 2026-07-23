library verilog;
use verilog.vl_types.all;
entity frequency_divider_new is
    port(
        clk_50mhz       : in     vl_logic;
        rst             : in     vl_logic;
        q_in            : in     vl_logic_vector(3 downto 0);
        clr_n           : in     vl_logic;
        ld_n            : in     vl_logic;
        enp             : in     vl_logic;
        ent             : in     vl_logic;
        rco             : out    vl_logic;
        q_out           : out    vl_logic_vector(3 downto 0);
        clk_1hz         : out    vl_logic;
        clk_10hz        : out    vl_logic;
        clk_100hz       : out    vl_logic;
        clk_1000hz      : out    vl_logic
    );
end frequency_divider_new;
