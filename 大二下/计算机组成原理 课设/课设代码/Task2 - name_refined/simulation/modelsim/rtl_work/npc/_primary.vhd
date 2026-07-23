library verilog;
use verilog.vl_types.all;
entity npc is
    port(
        PC              : in     vl_logic_vector(31 downto 0);
        Instr_25_0      : in     vl_logic_vector(25 downto 0);
        \register\      : in     vl_logic_vector(31 downto 0);
        PCSrc           : in     vl_logic_vector(1 downto 0);
        zero            : in     vl_logic;
        NPC             : out    vl_logic_vector(31 downto 0);
        pc_add4         : out    vl_logic_vector(31 downto 0)
    );
end npc;
