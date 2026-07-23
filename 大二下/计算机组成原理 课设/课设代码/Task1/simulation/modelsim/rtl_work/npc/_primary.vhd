library verilog;
use verilog.vl_types.all;
entity npc is
    port(
        PC              : in     vl_logic_vector(31 downto 0);
        SignImm         : in     vl_logic_vector(31 downto 0);
        Instr_25_0      : in     vl_logic_vector(25 downto 0);
        JR_Addr         : in     vl_logic_vector(31 downto 0);
        PCSrc           : in     vl_logic_vector(1 downto 0);
        NPC             : out    vl_logic_vector(31 downto 0)
    );
end npc;
