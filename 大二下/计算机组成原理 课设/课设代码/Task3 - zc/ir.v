module ir(irwr,clk,irin,irout);
    input clk, irwr;
    input [31:0] irin;
    output reg [31:0] irout;
    always@(posedge clk)
        if(irwr)
            irout <= irin;
        else
            $display("Can't write to ir");

endmodule