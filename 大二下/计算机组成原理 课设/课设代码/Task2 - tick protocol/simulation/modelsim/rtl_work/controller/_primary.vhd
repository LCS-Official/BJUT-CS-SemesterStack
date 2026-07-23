library verilog;
use verilog.vl_types.all;
entity controller is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        op              : in     vl_logic_vector(5 downto 0);
        funct           : in     vl_logic_vector(5 downto 0);
        zero            : in     vl_logic;
        overflow        : in     vl_logic;
        pc_write        : out    vl_logic;
        ir_write        : out    vl_logic;
        reg_write       : out    vl_logic;
        mem_read        : out    vl_logic;
        mem_write       : out    vl_logic;
        sign_ext_en     : out    vl_logic;
        reg_dst         : out    vl_logic_vector(1 downto 0);
        alu_src_a       : out    vl_logic_vector(1 downto 0);
        alu_src_b       : out    vl_logic_vector(1 downto 0);
        mem_to_reg      : out    vl_logic_vector(1 downto 0);
        next_pc_sel     : out    vl_logic_vector(1 downto 0);
        alu_op          : out    vl_logic_vector(3 downto 0);
        dm_data_size    : out    vl_logic_vector(1 downto 0)
    );
end controller;
