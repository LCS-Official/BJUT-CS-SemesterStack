module mips_test; 
  reg clk ;
  reg rst ;
  reg[31:0] in;

  integer i;

  mips m1(clk, rst, in);
  
  initial
    begin
        $readmemh("main.txt", m1.i1.im, 0, 'h1000);
        $readmemh("code_two.txt", m1.i1.im,'h180, 'hFFF);

        $monitor("Pc=%8x,irout=%8x",m1.i1.addr[9:2],m1.ir1.irout);
        $display("---");
        $display("---");

        in = 32'h1234;
        clk = 0;
        rst = 0;
        
        #5 rst = 1;
        #10 rst = 0;

        #5000 in = 32'h5678;
        #10000 $finish;
    end
    
    
  always
    #10 clk = ~clk;
  
endmodule