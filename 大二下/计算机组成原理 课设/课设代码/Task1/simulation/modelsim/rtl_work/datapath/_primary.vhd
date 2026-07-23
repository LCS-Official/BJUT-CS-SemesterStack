library verilog;
use verilog.vl_types.all;
entity datapath is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        RegWrite        : in     vl_logic;
        ExtOp           : in     vl_logic;
        ALUOp           : in     vl_logic_vector(3 downto 0);
        PCSrc           : in     vl_logic_vector(1 downto 0);
        RegDst          : in     vl_logic;
        ALUSrc          : in     vl_logic;
        MemWrite        : in     vl_logic;
        WriteBackSel    : in     vl_logic_vector(1 downto 0);
        JAL_Write       : in     vl_logic;
        Ovf_WriteEnable : in     vl_logic;
        Instr           : out    vl_logic_vector(31 downto 0);
        ALU_Zero        : out    vl_logic;
        ALU_Overflow    : out    vl_logic;
        GPR_RD1_Sign    : out    vl_logic
    );
end datapath;
