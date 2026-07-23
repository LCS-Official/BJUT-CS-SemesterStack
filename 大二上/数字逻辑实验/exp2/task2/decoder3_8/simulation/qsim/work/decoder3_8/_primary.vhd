library verilog;
use verilog.vl_types.all;
entity decoder3_8 is
    port(
        \in\            : in     vl_logic_vector(2 downto 0);
        out1            : out    vl_logic;
        out2            : out    vl_logic;
        out3            : out    vl_logic;
        out4            : out    vl_logic;
        out5            : out    vl_logic;
        out6            : out    vl_logic;
        out7            : out    vl_logic;
        out8            : out    vl_logic
    );
end decoder3_8;
