library verilog;
use verilog.vl_types.all;
entity datapath is
    port(
        clk             : in     vl_logic;
        rst             : in     vl_logic;
        pc_write        : in     vl_logic;
        ir_write        : in     vl_logic;
        reg_write       : in     vl_logic;
        mem_read        : in     vl_logic;
        mem_write       : in     vl_logic;
        sign_ext_en     : in     vl_logic;
        reg_dst         : in     vl_logic_vector(1 downto 0);
        gpr_dst_load    : in     vl_logic;
        alu_src_a       : in     vl_logic_vector(1 downto 0);
        alu_src_b       : in     vl_logic_vector(1 downto 0);
        mem_to_reg      : in     vl_logic_vector(1 downto 0);
        next_pc_sel     : in     vl_logic_vector(1 downto 0);
        alu_op          : in     vl_logic_vector(3 downto 0);
        dm_data_size    : in     vl_logic_vector(1 downto 0);
        op              : out    vl_logic_vector(5 downto 0);
        funct           : out    vl_logic_vector(5 downto 0);
        zero            : out    vl_logic;
        overflow        : out    vl_logic
    );
end datapath;
