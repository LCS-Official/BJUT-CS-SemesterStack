library verilog;
use verilog.vl_types.all;
entity datapath is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        RegWrite        : in     vl_logic;
        MemWrite        : in     vl_logic;
        PCWrite         : in     vl_logic;
        IRWrite         : in     vl_logic;
        ExtOp           : in     vl_logic;
        PCSrc           : in     vl_logic_vector(1 downto 0);
        ALUSrcA         : in     vl_logic_vector(1 downto 0);
        ALUSrcB         : in     vl_logic_vector(1 downto 0);
        WriteBackSel    : in     vl_logic_vector(1 downto 0);
        GPRWriteAddrSel : in     vl_logic_vector(1 downto 0);
        ALUOp           : in     vl_logic_vector(3 downto 0);
        Opcode          : out    vl_logic_vector(5 downto 0);
        Funct           : out    vl_logic_vector(5 downto 0);
        ALU_Zero        : out    vl_logic
    );
end datapath;
