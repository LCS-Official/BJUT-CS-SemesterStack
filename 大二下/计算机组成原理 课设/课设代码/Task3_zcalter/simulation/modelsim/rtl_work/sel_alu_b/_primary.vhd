library verilog;
use verilog.vl_types.all;
entity sel_alu_b is
    port(
        BSel            : in     vl_logic;
        bout            : in     vl_logic_vector(31 downto 0);
        imm32           : in     vl_logic_vector(31 downto 0);
        alu_b           : out    vl_logic_vector(31 downto 0)
    );
end sel_alu_b;
