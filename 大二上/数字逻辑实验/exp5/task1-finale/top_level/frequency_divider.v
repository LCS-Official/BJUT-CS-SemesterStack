module frequency_divider(clk_50mhz,clk_1000hz);
input clk_50mhz;
output clk_1000hz;
reg clk_1000hz;
reg [31:0]cnt1;
//parameter A=500000;	//splits 500000 into 1000hz and etc.
parameter A = 2;
always@(posedge clk_50mhz)
begin
  if(cnt1<(A/2-1)/10)
    cnt1<=cnt1+1'b1;
  else
    begin
	   cnt1<=1'b0;
		clk_1000hz<=~clk_1000hz;
	 end
end
endmodule	 