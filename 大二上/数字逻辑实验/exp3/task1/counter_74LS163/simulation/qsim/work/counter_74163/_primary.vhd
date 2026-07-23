library verilog;
use verilog.vl_types.all;
entity counter_74163 is
    port(
        clrn            : in     vl_logic;
        ldn             : in     vl_logic;
        enp             : in     vl_logic;
        ent             : in     vl_logic;
        clk             : in     vl_logic;
        Q_in            : in     vl_logic_vector(3 downto 0);
        Q_out           : out    vl_logic_vector(3 downto 0);
        rco             : out    vl_logic
    );
end counter_74163;
