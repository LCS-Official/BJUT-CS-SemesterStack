module liu_water_light(reset,out,clk_1hz);
input reset;
input clk_1hz;

output reg[15:0]out;
reg [4:0]state;

parameter ste0=0,ste1=1,ste2=2,ste3=3,ste4=4,ste5=5,ste6=6,ste7=7,ste8=8,ste9=9,ste10=10,ste11=11,ste12=12,ste13=13,ste14=14,ste15=15,ste16=16;

always @(state) begin
case (state)
    ste0:out=16'b1111_1111_1111_1111;
	 ste1:out=16'b1111_1111_1111_1110;
	 ste2:out=16'b1111_1111_1111_1101;
	 ste3:out=16'b1111_1111_1111_1011;
	 ste4:out=16'b1111_1111_1111_0111;
	 ste5:out=16'b1111_1111_1110_1111;
	 ste6:out=16'b1111_1111_1101_1111;
	 ste7:out=16'b1111_1111_1011_1111;
	 ste8:out=16'b1111_1111_0111_1111;
	 ste9:out=16'b1111_1110_1111_1111;
	 ste10:out=16'b1111_1101_1111_1111;
	 ste11:out=16'b1111_1011_1111_1111;
	 ste12:out=16'b1111_0111_1111_1111;
	 ste13:out=16'b1110_1111_1111_1111;
	 ste14:out=16'b1101_1111_1111_1111;
	 ste15:out=16'b1011_1111_1111_1111;
	 ste16:out=16'b0111_1111_1111_1111;
	 default: out=16'b1111_1111_1111_1111;
  endcase
end

always @(posedge clk_1hz)  
begin
  if(!reset)
    state=ste0;
  else
    case (state)
      ste0:state<=ste1;
		ste1:state<=ste2;
		ste2:state<=ste3;
		ste3:state<=ste4;
		ste4:state<=ste5;
		ste5:state<=ste6;
		ste6:state<=ste7;
      ste7:state<=ste8;
		ste8:state<=ste9;
		ste9:state<=ste10;
      ste10:state<=ste11;
      ste11:state<=ste12;
      ste12:state<=ste13;
      ste13:state<=ste14;
		ste14:state<=ste15;
		ste15:state<=ste16;
		ste16:state<=ste0;
		default state<=ste0;
    endcase
end  
endmodule