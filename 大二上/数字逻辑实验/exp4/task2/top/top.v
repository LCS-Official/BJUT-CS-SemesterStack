module top(clk,clr,rst,reset,z,c_state,n_state); 
	input clk,clr,reset,rst; 
	
	output z;
	output [3:0] c_state,n_state;
	
	wire clk_1hz;
	wire dout; 
	
	frequency_divider(.clk_50mhz(clk),.rst(rst),.clk_1hz(clk_1hz)); 
	data_generator(.clk(clk_1hz),.clr(clr),.dout(dout)); 
	seqdetector(.clk(clk_1hz),.x(dout),.reset(reset),.z(z),.c_state(c_state),.n_state(n_state)); 
	
endmodule