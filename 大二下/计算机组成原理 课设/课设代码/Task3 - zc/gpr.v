//same
module gpr(clk, reset, regwrite,gpr_rd, gpr_datain, rs, rt, busa, busb,overflow);
  input clk, reset, regwrite;//写允许信号
  input overflow;//恢复溢出用 溢出后 若不再溢出 恢复为0
  input [31:0] gpr_datain;//要写入的数据
  input [4:0] rs, rt, gpr_rd;//目的寄存器
  output [31:0] busa, busb;

  reg [31:0] reg_array [31:0];
  
  assign busa = reg_array[rs];
  assign busb = reg_array[rt];
  
  integer i;
  
  initial begin
    for(i = 0; i < 32; i = i + 1)  begin
      reg_array[i] <= 0;
    end
    
  end
  
  always@(posedge clk) begin
    $display("rd=%8X",gpr_rd);

    //if(overflow==0 && reg_array[30][0]==1) reg_array[30][0]<=0;

    if(reset) begin
      for(i = 0; i < 32; i = i + 1) reg_array[i] <= 0;
    end
    
    else  begin
      if(!regwrite)
        $display("Can't write to GPR");
      else
        // judge $0
        if(gpr_rd == 5'b00000)
          $display("Can't change reg 0");
        //else if(overflow) reg_array[gpr_rd][0]<=gpr_datain[0];
        else
          reg_array[gpr_rd] <= gpr_datain;

          $display("Write to GPR");
          $display("R[00-07]=%8X,%8X,%8X,%8X,%8X,%8X,%8X,%8X",00000000,reg_array[1],reg_array[2],reg_array[3],reg_array[4],reg_array[5],reg_array[6],reg_array[7]);
          $display("R[08-15]=%8X,%8X,%8X,%8X,%8X,%8X,%8X,%8X",reg_array[8],reg_array[9],reg_array[10],reg_array[11],reg_array[12],reg_array[13],reg_array[14],reg_array[15]);
          $display("R[16-23]=%8X,%8X,%8X,%8X,%8X,%8X,%8X,%8X",reg_array[16],reg_array[17],reg_array[18],reg_array[19],reg_array[20],reg_array[21],reg_array[22],reg_array[23]);
          $display("R[24-31]=%8X,%8X,%8X,%8X,%8X,%8X,%8X,%8X",reg_array[24],reg_array[25],reg_array[26],reg_array[27],reg_array[28],reg_array[29],reg_array[30],reg_array[31]);
    end

    if(!overflow) reg_array[30][0]<=0;
  end


endmodule