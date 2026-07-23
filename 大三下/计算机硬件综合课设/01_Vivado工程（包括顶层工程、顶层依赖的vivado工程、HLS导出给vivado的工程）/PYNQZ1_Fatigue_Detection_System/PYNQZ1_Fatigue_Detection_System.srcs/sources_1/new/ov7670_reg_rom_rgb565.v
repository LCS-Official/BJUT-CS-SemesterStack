`timescale 1ns / 1ps

module ov7670_reg_rom_rgb565 (
    input  wire [7:0] index,

    output reg  [7:0] reg_addr,
    output reg  [7:0] reg_data,
    output reg        valid,
    output reg        last
);

    always @(*) begin
        reg_addr = 8'h00;
        reg_data = 8'h00;
        valid    = 1'b1;
        last     = 1'b0;

        case (index)
            8'd0: begin
                reg_addr = 8'h11;
                reg_data = 8'h00;
            end

            8'd1: begin
                reg_addr = 8'h12;
                reg_data = 8'h04;
            end

           
            8'd2: begin
                reg_addr = 8'h0C;
                reg_data = 8'h00;
            end

            8'd3: begin
                reg_addr = 8'h3E;
                reg_data = 8'h00;
            end

            8'd4: begin
                reg_addr = 8'h70;
                reg_data = 8'h3A;
            end

            8'd5: begin
                reg_addr = 8'h71;
                reg_data = 8'h35;
            end

            8'd6: begin
                reg_addr = 8'h72;
                reg_data = 8'h00;
            end

            8'd7: begin
                reg_addr = 8'h73;
                reg_data = 8'hF0;
            end

            8'd8: begin
                reg_addr = 8'hA2;
                reg_data = 8'h02;
            end

            8'd9: begin
                reg_addr = 8'h8C;
                reg_data = 8'h00;
            end

            8'd10: begin
                reg_addr = 8'h40;
                reg_data = 8'hD0;
            end

            8'd11: begin
                reg_addr = 8'h3A;
                reg_data = 8'h04;
            end

         
            8'd12: begin
                reg_addr = 8'h3D;
                reg_data = 8'hC0;
            end

            
            8'd13: begin
                reg_addr = 8'h15;
                reg_data = 8'h00;
            end

            8'd14: begin
                reg_addr = 8'h17;
                reg_data = 8'h13;
            end

            
            8'd15: begin
                reg_addr = 8'h18;
                reg_data = 8'h01;
            end

            
            8'd16: begin
                reg_addr = 8'h32;
                reg_data = 8'hB6;
            end

            
            8'd17: begin
                reg_addr = 8'h19;
                reg_data = 8'h02;
            end

            
            8'd18: begin
                reg_addr = 8'h1A;
                reg_data = 8'h7A;
            end

            
            8'd19: begin
                reg_addr = 8'h03;
                reg_data = 8'h0A;
            end

            8'd20: begin
                reg_addr = 8'h0F;
                reg_data = 8'h4B;
            end

            8'd21: begin
                reg_addr = 8'h1E;
                reg_data = 8'h07;
            end

            8'd22: begin
                reg_addr = 8'h13;
                reg_data = 8'hE7;
            end

            8'd23: begin
                reg_addr = 8'h14;
                reg_data = 8'h38;
            end

            8'd24: begin
                reg_addr = 8'hA5;
                reg_data = 8'h05;
            end

            8'd25: begin
                reg_addr = 8'hAB;
                reg_data = 8'h07;
            end

            8'd26: begin
                reg_addr = 8'h24;
                reg_data = 8'h95;
            end

            8'd27: begin
                reg_addr = 8'h25;
                reg_data = 8'h33;
            end

            8'd28: begin
                reg_addr = 8'h26;
                reg_data = 8'hE3;
            end

            8'd29: begin
                reg_addr = 8'h9F;
                reg_data = 8'h78;
            end

            8'd30: begin
                reg_addr = 8'hA0;
                reg_data = 8'h68;
            end

            8'd31: begin
                reg_addr = 8'hA1;
                reg_data = 8'h03;
            end

            8'd32: begin
                reg_addr = 8'hA6;
                reg_data = 8'hD8;
            end

            8'd33: begin
                reg_addr = 8'hA7;
                reg_data = 8'hD8;
            end

            8'd34: begin
                reg_addr = 8'hA8;
                reg_data = 8'hF0;
            end

            8'd35: begin
                reg_addr = 8'hA9;
                reg_data = 8'h90;
            end

            8'd36: begin
                reg_addr = 8'hAA;
                reg_data = 8'h94;
            end

           
            8'd37: begin
                reg_addr = 8'h4F;
                reg_data = 8'h80;
            end

            8'd38: begin
                reg_addr = 8'h50;
                reg_data = 8'h80;
            end

            8'd39: begin
                reg_addr = 8'h51;
                reg_data = 8'h00;
            end

            8'd40: begin
                reg_addr = 8'h52;
                reg_data = 8'h22;
            end

            8'd41: begin
                reg_addr = 8'h53;
                reg_data = 8'h5E;
            end

            8'd42: begin
                reg_addr = 8'h54;
                reg_data = 8'h80;
            end

            8'd43: begin
                reg_addr = 8'h58;
                reg_data = 8'h9E;
            end

           
            8'd44: begin
                reg_addr = 8'h41;
                reg_data = 8'h08;
            end

            8'd45: begin
                reg_addr = 8'h3F;
                reg_data = 8'h00;
            end

            8'd46: begin
                reg_addr = 8'h75;
                reg_data = 8'h05;
            end

            8'd47: begin
                reg_addr = 8'h76;
                reg_data = 8'hE1;
            end

            8'd48: begin
                reg_addr = 8'h4C;
                reg_data = 8'h00;
            end

            8'd49: begin
                reg_addr = 8'h77;
                reg_data = 8'h01;
            end

            8'd50: begin
                reg_addr = 8'h4B;
                reg_data = 8'h09;
            end

            8'd51: begin
                reg_addr = 8'hC9;
                reg_data = 8'h60;
            end

            8'd52: begin
                reg_addr = 8'h56;
                reg_data = 8'h40;
            end

            8'd53: begin
                reg_addr = 8'h34;
                reg_data = 8'h11;
            end

            8'd54: begin
                reg_addr = 8'h3B;
                reg_data = 8'h02;
            end

            8'd55: begin
                reg_addr = 8'hA4;
                reg_data = 8'h89;
            end

            8'd56: begin
                reg_addr = 8'h96;
                reg_data = 8'h00;
            end

            8'd57: begin
                reg_addr = 8'h7A;
                reg_data = 8'h20;
            end

            8'd58: begin
                reg_addr = 8'h7B;
                reg_data = 8'h10;
            end

            8'd59: begin
                reg_addr = 8'h7C;
                reg_data = 8'h1E;
            end

            8'd60: begin
                reg_addr = 8'h7D;
                reg_data = 8'h35;
            end

            8'd61: begin
                reg_addr = 8'h7E;
                reg_data = 8'h5A;
            end

            8'd62: begin
                reg_addr = 8'h7F;
                reg_data = 8'h69;
            end

            8'd63: begin
                reg_addr = 8'h80;
                reg_data = 8'h76;
            end

            8'd64: begin
                reg_addr = 8'h81;
                reg_data = 8'h80;
            end

            8'd65: begin
                reg_addr = 8'h82;
                reg_data = 8'h88;
            end

            8'd66: begin
                reg_addr = 8'h83;
                reg_data = 8'h8F;
            end

            8'd67: begin
                reg_addr = 8'h84;
                reg_data = 8'h96;
            end

            8'd68: begin
                reg_addr = 8'h85;
                reg_data = 8'hA3;
            end

            8'd69: begin
                reg_addr = 8'h86;
                reg_data = 8'hAF;
            end

            8'd70: begin
                reg_addr = 8'h87;
                reg_data = 8'hC4;
            end

            8'd71: begin
                reg_addr = 8'h88;
                reg_data = 8'hD7;
            end

            8'd72: begin
                reg_addr = 8'h89;
                reg_data = 8'hE8;
            end

            8'd73: begin
                reg_addr = 8'h43;
                reg_data = 8'h14;
            end

            8'd74: begin
                reg_addr = 8'h44;
                reg_data = 8'hF0;
            end

            8'd75: begin
                reg_addr = 8'h45;
                reg_data = 8'h34;
            end

            8'd76: begin
                reg_addr = 8'h46;
                reg_data = 8'h58;
            end

            8'd77: begin
                reg_addr = 8'h47;
                reg_data = 8'h28;
            end

            8'd78: begin
                reg_addr = 8'h48;
                reg_data = 8'h3A;
            end

            8'd79: begin
                reg_addr = 8'h59;
                reg_data = 8'h88;
            end

            8'd80: begin
                reg_addr = 8'h5A;
                reg_data = 8'h88;
            end

            8'd81: begin
                reg_addr = 8'h5B;
                reg_data = 8'h44;
            end

            8'd82: begin
                reg_addr = 8'h5C;
                reg_data = 8'h67;
            end

            8'd83: begin
                reg_addr = 8'h5D;
                reg_data = 8'h49;
            end

            8'd84: begin
                reg_addr = 8'h5E;
                reg_data = 8'h0E;
            end

            8'd85: begin
                reg_addr = 8'h6C;
                reg_data = 8'h0A;
            end

            8'd86: begin
                reg_addr = 8'h6D;
                reg_data = 8'h55;
            end

            8'd87: begin
                reg_addr = 8'h6E;
                reg_data = 8'h11;
            end

            8'd88: begin
                reg_addr = 8'h6F;
                reg_data = 8'h9F;
            end

            8'd89: begin
                reg_addr = 8'h6A;
                reg_data = 8'h40;
            end
            8'd90: begin
                reg_addr = 8'h01;
                reg_data = 8'h40;
            end

            8'd91: begin
                reg_addr = 8'h02;
                reg_data = 8'h40;
            end
            8'd92: begin
                reg_addr = 8'h42;
                reg_data = 8'h00;
                last     = 1'b1;
            end

            default: begin
                reg_addr = 8'hFF;
                reg_data = 8'hFF;
                valid    = 1'b0;
                last     = 1'b0;
            end

        endcase
    end

endmodule