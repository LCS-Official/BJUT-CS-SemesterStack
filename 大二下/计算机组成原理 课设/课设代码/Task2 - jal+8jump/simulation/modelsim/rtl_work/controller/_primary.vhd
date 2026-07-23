library verilog;
use verilog.vl_types.all;
entity controller is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        Opcode          : in     vl_logic_vector(5 downto 0);
        Funct           : in     vl_logic_vector(5 downto 0);
        ALU_Zero        : in     vl_logic;
        RegWrite        : out    vl_logic;
        MemWrite        : out    vl_logic;
        PCWrite         : out    vl_logic;
        IRWrite         : out    vl_logic;
        ExtOp           : out    vl_logic;
        PCSrc           : out    vl_logic_vector(1 downto 0);
        ALUSrcA         : out    vl_logic_vector(1 downto 0);
        ALUSrcB         : out    vl_logic_vector(1 downto 0);
        WriteBackSel    : out    vl_logic_vector(1 downto 0);
        GPRWriteAddrSel : out    vl_logic_vector(1 downto 0);
        ALUOp           : out    vl_logic_vector(3 downto 0)
    );
end controller;
