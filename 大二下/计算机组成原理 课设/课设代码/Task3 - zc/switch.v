module switch(in,out);
    input[31:0] in;//32位输入开关值 在test里面赋初值
    output[31:0] out;//计数的初值
    assign out = in;
endmodule