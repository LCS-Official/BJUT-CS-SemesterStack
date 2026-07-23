module test;
    reg [31:0] pcin;
    reg clk;
    wire [31:0] pcout;

    pc p1(clk, pcin, pcout);

    initial 
        begin
            clk=1;
            pcin=32'h0000_3000;


            #50 pcin=32'h3410_0001;
            #30 pcin=32'h3411_0003;
            
            #1000 $finish;

            
        end

    always
        begin
            #30 clk=~clk;
        end

    initial 
        begin
            $dumpfile("wave.vcd");
            $dumpvars(0,test);
        end

endmodule