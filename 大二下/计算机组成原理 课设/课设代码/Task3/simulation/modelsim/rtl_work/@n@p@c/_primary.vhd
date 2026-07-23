library verilog;
use verilog.vl_types.all;
entity NPC is
    port(
        PC              : in     vl_logic_vector(31 downto 0);
        rd1             : in     vl_logic_vector(31 downto 0);
        NPC_Op          : in     vl_logic_vector(1 downto 0);
        zero            : in     vl_logic;
        imm26           : in     vl_logic_vector(25 downto 0);
        NPC             : out    vl_logic_vector(31 downto 0);
        PC_plus4        : out    vl_logic_vector(31 downto 0);
        rst             : in     vl_logic;
        epc             : in     vl_logic_vector(31 downto 0);
        ERET            : in     vl_logic;
        IntReq          : in     vl_logic
    );
end NPC;
