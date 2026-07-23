module counter_74163(clrn, ldn, enp, ent, clk, Q_in, Q_out, rco);
	input clrn, ldn, enp, ent, clk;
	input [3:0] Q_in;
	output [3:0] Q_out;
	output rco;
	reg [3:0] Q_out;
	assign rco = (Q_out == 4'b1111 && ent == 1) ? 1 : 0;
	always @ (posedge clk)
		begin
			if(~clrn)
				Q_out <= 0;
			else if(~ldn)
				Q_out <= Q_in;
			else if(enp == 1 && ent == 1)
				Q_out <= Q_out + 1;
		end
endmodule