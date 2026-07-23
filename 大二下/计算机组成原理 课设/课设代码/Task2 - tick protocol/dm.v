// dm.v
module dm(
    input clk,
    input mem_read,
    input mem_write,
    input [31:0] addr,
    input [31:0] write_data,
    input [1:0] data_size, // 00: byte, 01: half-word(not used), 10: word
    output [31:0] read_data
);
    // 1KB = 1024 Bytes
    reg [7:0] mem [1023:0];
    
    reg [31:0] read_data_reg;

    // 小端序写入
    always @(posedge clk) begin
        if (mem_write) begin
            case (data_size)
                2'b10: begin // sw (word)
                    mem[addr] <= write_data[7:0];
                    mem[addr+1] <= write_data[15:8];
                    mem[addr+2] <= write_data[23:16];
                    mem[addr+3] <= write_data[31:24];
                end
                2'b00: begin // sb (byte)
                    mem[addr] <= write_data[7:0];
                end
            endcase
        end
    end

    // 组合逻辑读，小端序
    always @(*) begin
        if(mem_read) begin
             case (data_size)
                2'b10: // lw (word)
                    read_data_reg = {mem[addr+3], mem[addr+2], mem[addr+1], mem[addr]};
                2'b00: // lb (byte)
                    read_data_reg = {{24{mem[addr+0][7]}}, mem[addr+0]}; // 符号扩展
                default:
                    read_data_reg = 32'hxxxxxxxx;
            endcase
        end else begin
            read_data_reg = 32'hxxxxxxxx;
        end
    end
    
    assign read_data = read_data_reg;

endmodule