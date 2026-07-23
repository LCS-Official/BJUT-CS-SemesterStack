module test_mips_tb; 
  reg clk ;
  reg rst ;
  reg[31:0] in;

  mips m1(clk, rst, in);
  

  initial
    begin
      // 文件加载部分保持不变
     $readmemh("code_main.txt", m1.IM.im, 0); 
	  $readmemh("code_two.txt", m1.IM.im, 'h180);

    // 监控部分保持不变
    $monitor("Time=%0t, PC=%08h, Instruction=%08h", $time, m1.PC, m1.IR.irout);
    $display("--- Memory Initialized ---");


    clk = 0;
    rst = 1;      // 1. 仿真开始时，立即让处理器进入复位状态
    #25;          // 2. 保持复位状态超过一个时钟周期 (你的周期是20ns)，确保至少被一个上升沿采到
    rst = 0;      // 3. 撤销复位，处理器从下一拍开始正常工作
    // =======================================================

    // 后续的输入激励和仿真结束控制
    in = 32'h1234;
    #5000 in = 32'h5678;
    #30000 $finish;
    end
    
    
  always
    #10 clk = ~clk;

  
endmodule