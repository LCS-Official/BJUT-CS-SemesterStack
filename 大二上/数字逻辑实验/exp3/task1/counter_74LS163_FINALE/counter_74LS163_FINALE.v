module counter_74LS163_FINALE(clrn, ldn, enp, ent, clk, Q_in, rco, n_en, LED_out, sel);

	input clrn, ldn, enp, ent, clk, n_en;
	input [3:0] Q_in;
	
	output rco, sel;
	output [6:0] LED_out;
	
	wire [3:0] data;

	counter_74LS163 counter_74LS163_ind	//74LS163 INDIVIDUAL claim
	(
		.clrn(clrn) ,
		.ldn(ldn) ,
		.enp(enp) ,
		.ent(ent) ,
		.clk(clk) ,
		.Q_in(Q_in) ,
		.Q_out(data) ,
		.rco(rco)
	);
	
	BCD_7seg BCD_7seg_ind //BCD INDIVIDUAL claim
	(
		.n_en(n_en) ,
		.LED_in(data) ,
		.LED_out(LED_out) ,
		.sel(sel)
	);
	
endmodule