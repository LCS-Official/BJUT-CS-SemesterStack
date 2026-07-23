module dm_1k(addr, din, we, clk, dout,lb,sb);
	input[9:0] addr;
	input[31:0] din;
	input we;
	input clk;
	input lb,sb;
	
	output[31:0] dout;

	reg[7:0] dm[12287:0];
	
	wire[7:0] templb;
	wire[31:0] templb2;
	wire[7:0] tempsb;
	
	integer i;

	initial begin
		for(i = 0; i < 1024; i = i+1) dm[i] <= 0;
	end

	assign templb = dm[addr];
	assign templb2= {{24{templb[7]}},templb};

	assign tempsb = din[7:0];

	assign dout = (lb==1)?templb2: {dm[addr+3], dm[addr+2], dm[addr+1], dm[addr]};
  
	always @(posedge clk)
		if(we) begin
			$display("Write to dm,the start address:%10X, change to %8X",addr[9:0],din);
			if(sb) dm[addr]<=tempsb;
			else {dm[addr+3], dm[addr+2], dm[addr+1], dm[addr]} <= {din[31:24], din[23:16], din[15:8], din[7:0]}; //小端序存
		end
		else $display("无法写入dm");

endmodule