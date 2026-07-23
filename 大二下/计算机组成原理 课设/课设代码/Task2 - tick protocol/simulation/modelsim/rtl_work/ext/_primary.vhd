library verilog;
use verilog.vl_types.all;
entity ext is
    port(
        imm             : in     vl_logic_vector(15 downto 0);
        sign_ext        : in     vl_logic;
        ext_imm         : out    vl_logic_vector(31 downto 0)
    );
end ext;
