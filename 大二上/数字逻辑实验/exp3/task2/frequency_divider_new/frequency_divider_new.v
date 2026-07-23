module frequency_divider_new(clrn, ldn, enp, ent, Q_in, rco,sel, rst, clk_50mhz, clk_1khz, clk_100hz, clk_10hz, LED_out);
	input clrn, ldn, enp, ent, rst, clk_50mhz;
	input [3:0] Q_in;
	output rco, clk_1khz, clk_100hz, clk_10hz,sel;

	wire clk_1hz;
	
	output [6:0] LED_out;
	wire [3:0] data;
	
	counter_74163 counter_74163_inst
	(
		.clrn(clrn) ,
		.ldn(ldn) ,
		.enp(enp) ,
		.ent(ent) ,
		.clk(clk_1hz) ,
		.Q_in(Q_in) ,
		.Q_out(data) ,
		.rco(rco)
	);
	
		BCD_7seg BCD_7seg_inst //BCD INDIVIDUAL claim
	(
		.n_en(n_en) ,
		.LED_in(data) ,
		.LED_out(LED_out) ,
		.sel(sel)
	);
	
	frequency_divider frequency_divider_inst
	(
		.clk_50mhz(clk_50mhz) ,
		.rst(rst) ,
		.clk_1khz(clk_1khz) ,
		.clk_100hz(clk_100hz) ,
		.clk_10hz(clk_10hz) ,
		.clk_1hz(clk_1hz)
	);
endmodule