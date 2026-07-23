module test;
    reg [25:0] imm;//指令低26位 j指令
    reg [31:0] pcin;//输入的pc
    reg [31:0] rd1;//jr 跳转的寄存器中地址
    reg zero, rst;//是否结果是0 beq 共同决定是否跳转
    reg [1:0] npcop;//00 pc4 01 beq 10 jal 11 jr
    wire [31:0] nextpc;
    wire [31:0] pc_4;//jal要存入pc+4到寄存器中 返回地址

    npc n1(pcin, rd1, npcop, zero, imm, nextpc, pc_4, rst);

    initial 
        begin
            
            #1000 $finish;

            $dumpfile("test.vcd");
            $dumpvars(0,test);
        end

    always
        begin
            #30 clk=~clk;
        end

endmodule