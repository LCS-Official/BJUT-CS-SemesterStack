module IM(addr, dout);
	input [12:0] addr;
	output [31:0] dout;
	reg [7:0] RAM[8192:0];
    
	initial 
		begin
        $readmemh("P3 INITIAL.txt", RAM, 'h1000);
        $readmemh("P3 ISR.txt", RAM, 'h0180);
		end
  
	assign dout = {RAM[addr], RAM[addr+1], RAM[addr+2], RAM[addr+3]};
  
endmodule