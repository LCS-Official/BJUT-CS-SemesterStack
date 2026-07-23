library verilog;
use verilog.vl_types.all;
entity datapath is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        reg_sel         : in     vl_logic_vector(1 downto 0);
        WriteBackSel    : in     vl_logic_vector(1 downto 0);
        PCSrc           : in     vl_logic_vector(1 downto 0);
        ExtOp           : in     vl_logic_vector(1 downto 0);
        we              : in     vl_logic;
        RegWrite        : in     vl_logic;
        alu_sel         : in     vl_logic;
        addien          : in     vl_logic;
        slt_en          : in     vl_logic;
        lb_en           : in     vl_logic;
        sb_en           : in     vl_logic;
        pcwr            : in     vl_logic;
        IRWrite         : in     vl_logic;
        ALUOp           : in     vl_logic_vector(2 downto 0);
        Opcode          : out    vl_logic_vector(5 downto 0);
        Funct           : out    vl_logic_vector(5 downto 0);
        ALU_Zero        : out    vl_logic
    );
end datapath;
