module top(clk_50mhz,rst,out);

	input clk_50mhz, rst;
	
	wire clk_1hz;
	output [15:0] out;

	frequency_divider(.clk_50mhz(clk_50mhz), .rst(rst), .clk_1hz(clk_1hz));
	
	liu_water_light(.reset(rst), .out(out) ,.clk_1hz(clk_1hz)); //set instance liu_water_light
	
endmodule