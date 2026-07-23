library verilog;
use verilog.vl_types.all;
entity controller is
    port(
        Instr           : in     vl_logic_vector(31 downto 0);
        ALU_Zero        : in     vl_logic;
        ALU_Overflow    : in     vl_logic;
        GPR_RD1_Sign    : in     vl_logic;
        RegWrite        : out    vl_logic;
        ExtOp           : out    vl_logic;
        ALUOp           : out    vl_logic_vector(3 downto 0);
        PCSrc           : out    vl_logic_vector(1 downto 0);
        RegDst          : out    vl_logic;
        ALUSrc          : out    vl_logic;
        MemWrite        : out    vl_logic;
        WriteBackSel    : out    vl_logic_vector(1 downto 0);
        JAL_Write       : out    vl_logic;
        Ovf_WriteEnable : out    vl_logic
    );
end controller;
