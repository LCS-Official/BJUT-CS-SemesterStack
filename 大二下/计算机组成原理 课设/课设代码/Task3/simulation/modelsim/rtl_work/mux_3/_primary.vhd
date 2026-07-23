library verilog;
use verilog.vl_types.all;
entity mux_3 is
    port(
        B_sel           : in     vl_logic;
        ALU_B           : in     vl_logic_vector(31 downto 0);
        imm32           : in     vl_logic_vector(31 downto 0);
        m3out           : out    vl_logic_vector(31 downto 0)
    );
end mux_3;
