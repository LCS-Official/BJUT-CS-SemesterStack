module sel_led_23071005(
    input [3:0] in1,
    input [3:0] in2,
    input [2:0] sel,
	 input en,
    output reg [3:0] out
);
    reg [3:0] in3 = 4'b0000;
    reg [3:0] in4 = 4'b0001;
    reg [3:0] in5 = 4'b0111;
    reg [3:0] in6 = 4'b0000;	
    reg [3:0] in7 = 4'b0011;
    reg [3:0] in8 = 4'b0010;
    always @(*) begin
	  if(en) out=4'b0000;
     else case (sel)
            3'b000: out = in1;
            3'b001: out = in2;
            3'b010: out = in3;
            3'b011: out = in4;
            3'b100: out = in5;
            3'b101: out = in6;
            3'b110: out = in7;
            3'b111: out = in8;
            default: out = 4'b0000;
          endcase
    end
endmodule
