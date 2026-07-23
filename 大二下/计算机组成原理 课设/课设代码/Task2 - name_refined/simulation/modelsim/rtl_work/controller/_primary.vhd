library verilog;
use verilog.vl_types.all;
entity controller is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        op              : in     vl_logic_vector(5 downto 0);
        func            : in     vl_logic_vector(5 downto 0);
        zero            : in     vl_logic;
        PCSrc           : out    vl_logic_vector(1 downto 0);
        PCWrite         : out    vl_logic;
        IRWrite         : out    vl_logic;
        RegWrite        : out    vl_logic;
        RegDst          : out    vl_logic_vector(1 downto 0);
        MemToReg        : out    vl_logic_vector(1 downto 0);
        ExtOp           : out    vl_logic_vector(1 downto 0);
        ALUOp           : out    vl_logic_vector(2 downto 0);
        ALUSrc          : out    vl_logic;
        MemWrite        : out    vl_logic;
        lb_en           : out    vl_logic;
        sb_en           : out    vl_logic;
        slt_en          : out    vl_logic;
        addi_en         : out    vl_logic
    );
end controller;
