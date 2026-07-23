module gpr(clk, reset, regwrite, gpr_rd, gpr_datain, rs, rt, busa, busb, overflow);
  input clk, reset, regwrite, overflow;
  input [31:0] gpr_datain;
  input [4:0] rs, rt, gpr_rd;
  output [31:0] busa, busb;

  reg [31:0] reg_array [31:0];
  
  assign busa = reg_array[rs];
  assign busb = reg_array[rt];
  
  integer i;
  
	initial begin
		for(i = 0; i < 32; i = i + 1) begin
			reg_array[i] <= 0;
		end 
	end
  
	always@(posedge clk) begin
		$display("rd=%8X",gpr_rd);
		if(reset) begin
			for(i = 0; i < 32; i = i + 1) reg_array[i] <= 0;
		end
    
		else begin
			if(!regwrite)
				$display("Can't write to GPR");
			else if(gpr_rd == 5'b00000)
				$display("Can't change reg 0");
			else
				reg_array[gpr_rd] <= gpr_datain;
		end

		if(!overflow) reg_array[30][0]<=0;
  end
endmodule