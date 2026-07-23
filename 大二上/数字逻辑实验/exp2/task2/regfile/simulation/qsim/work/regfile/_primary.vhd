library verilog;
use verilog.vl_types.all;
entity regfile is
    port(
        out1            : out    vl_logic_vector(31 downto 0);
        clk             : in     vl_logic;
        rst_n           : in     vl_logic;
        w_r             : in     vl_logic;
        en1             : in     vl_logic;
        \in\            : in     vl_logic_vector(31 downto 0);
        out2            : out    vl_logic_vector(31 downto 0);
        en2             : in     vl_logic;
        out3            : out    vl_logic_vector(31 downto 0);
        en3             : in     vl_logic;
        out4            : out    vl_logic_vector(31 downto 0);
        en4             : in     vl_logic;
        out5            : out    vl_logic_vector(31 downto 0);
        en5             : in     vl_logic;
        out6            : out    vl_logic_vector(31 downto 0);
        en6             : in     vl_logic;
        out7            : out    vl_logic_vector(31 downto 0);
        en7             : in     vl_logic;
        out8            : out    vl_logic_vector(31 downto 0);
        en8             : in     vl_logic
    );
end regfile;
