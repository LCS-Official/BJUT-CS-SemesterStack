module frequency_divider(clk_50mhz,rst,clk_1hz,clk_10hz,clk_100hz,clk_1000hz);

input clk_50mhz,rst;
output reg clk_1hz,clk_10hz,clk_100hz,clk_1000hz;

reg [31:0]cnt1;
reg [31:0]cnt10;
reg [31:0]cnt100; 
reg [31:0]cnt1000;

parameter N1 = 10,N10=8,N100=4,N1000=2;

always @(posedge clk_50mhz) begin
    if (!rst) begin
        cnt1 <= 0;
        clk_1hz <= 0;
    end else if (cnt1 < N1/2 - 1) begin
        cnt1 <= cnt1 + 1'b1;
    end else begin
        cnt1 <= 0;
        clk_1hz <= ~clk_1hz;
    end
end

always @(posedge clk_50mhz) begin
    if (!rst) begin
        cnt10 <= 0;
        clk_10hz <= 0;
    end else if (cnt10 < N10/2 - 1) begin
        cnt10 <= cnt10 + 1'b1;
    end else begin
        cnt10 <= 0;
        clk_10hz <= ~clk_10hz;
    end
end

always @(posedge clk_50mhz) begin
    if (!rst) begin
        cnt100 <= 0;
        clk_100hz <= 0;
    end else if (cnt100 < N100/2 - 1) begin
        cnt100 <= cnt100 + 1'b1;
    end else begin
        cnt100 <= 0;
        clk_100hz <= ~clk_100hz;
    end
end

always @(posedge clk_50mhz) begin
    if (!rst) begin
        cnt1000 <= 0;
        clk_1000hz <= 0;
    end else if (cnt1000 < N1000/2 - 1) begin
        cnt1000 <= cnt1000 + 1'b1;
    end else begin
        cnt1000 <= 0;
        clk_1000hz <= ~clk_1000hz;
    end
end

endmodule

