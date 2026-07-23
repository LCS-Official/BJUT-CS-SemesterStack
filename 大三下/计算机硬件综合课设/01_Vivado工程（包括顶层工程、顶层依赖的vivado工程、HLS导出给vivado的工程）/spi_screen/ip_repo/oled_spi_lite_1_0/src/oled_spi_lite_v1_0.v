`timescale 1 ns / 1 ps

module oled_spi_lite_v1_0 #(
    parameter integer C_S00_AXI_DATA_WIDTH = 32,
    parameter integer C_S00_AXI_ADDR_WIDTH = 5
) (
    output wire oled_cs_n,
    output wire oled_dc,
    output wire oled_res_n,
    output wire oled_scl,
    output wire oled_sda,

    input wire s00_axi_aclk,
    input wire s00_axi_aresetn,
    input wire [C_S00_AXI_ADDR_WIDTH-1 : 0] s00_axi_awaddr,
    input wire [2 : 0] s00_axi_awprot,
    input wire s00_axi_awvalid,
    output wire s00_axi_awready,
    input wire [C_S00_AXI_DATA_WIDTH-1 : 0] s00_axi_wdata,
    input wire [(C_S00_AXI_DATA_WIDTH/8)-1 : 0] s00_axi_wstrb,
    input wire s00_axi_wvalid,
    output wire s00_axi_wready,
    output wire [1 : 0] s00_axi_bresp,
    output wire s00_axi_bvalid,
    input wire s00_axi_bready,
    input wire [C_S00_AXI_ADDR_WIDTH-1 : 0] s00_axi_araddr,
    input wire [2 : 0] s00_axi_arprot,
    input wire s00_axi_arvalid,
    output wire s00_axi_arready,
    output wire [C_S00_AXI_DATA_WIDTH-1 : 0] s00_axi_rdata,
    output wire [1 : 0] s00_axi_rresp,
    output wire s00_axi_rvalid,
    input wire s00_axi_rready
);

    localparam integer ADDR_LSB = (C_S00_AXI_DATA_WIDTH / 32) + 1;
    localparam integer OPT_MEM_ADDR_BITS = 2;

    reg [C_S00_AXI_ADDR_WIDTH-1 : 0] axi_awaddr;
    reg axi_awready;
    reg axi_wready;
    reg [1 : 0] axi_bresp;
    reg axi_bvalid;
    reg [C_S00_AXI_ADDR_WIDTH-1 : 0] axi_araddr;
    reg axi_arready;
    reg [C_S00_AXI_DATA_WIDTH-1 : 0] axi_rdata;
    reg [1 : 0] axi_rresp;
    reg axi_rvalid;

    assign s00_axi_awready = axi_awready;
    assign s00_axi_wready  = axi_wready;
    assign s00_axi_bresp   = axi_bresp;
    assign s00_axi_bvalid  = axi_bvalid;
    assign s00_axi_arready = axi_arready;
    assign s00_axi_rdata   = axi_rdata;
    assign s00_axi_rresp   = axi_rresp;
    assign s00_axi_rvalid  = axi_rvalid;

    reg aw_en;
    wire slv_reg_wren;
    wire slv_reg_rden;
    reg [C_S00_AXI_DATA_WIDTH-1:0] reg_data_out;
    integer byte_index;

    reg dc_reg;
    reg cs_n_reg;
    reg res_n_reg;
    reg [7:0] tx_data_reg;
    reg [15:0] clk_div_reg;
    reg start_pulse;

    reg busy_reg;
    reg done_toggle_reg;
    reg sclk_reg;
    reg sda_reg;
    reg [7:0] shift_reg;
    reg [2:0] bit_idx;
    reg [15:0] div_cnt;
    reg phase_reg;

    assign oled_cs_n  = cs_n_reg;
    assign oled_dc    = dc_reg;
    assign oled_res_n = res_n_reg;
    assign oled_scl   = sclk_reg;
    assign oled_sda   = sda_reg;

    always @(posedge s00_axi_aclk) begin
        if (!s00_axi_aresetn) begin
            axi_awready <= 1'b0;
            aw_en <= 1'b1;
        end else begin
            if (!axi_awready && s00_axi_awvalid && s00_axi_wvalid && aw_en) begin
                axi_awready <= 1'b1;
                aw_en <= 1'b0;
            end else if (s00_axi_bready && axi_bvalid) begin
                aw_en <= 1'b1;
                axi_awready <= 1'b0;
            end else begin
                axi_awready <= 1'b0;
            end
        end
    end

    always @(posedge s00_axi_aclk) begin
        if (!s00_axi_aresetn) begin
            axi_awaddr <= {C_S00_AXI_ADDR_WIDTH{1'b0}};
        end else if (!axi_awready && s00_axi_awvalid && s00_axi_wvalid && aw_en) begin
            axi_awaddr <= s00_axi_awaddr;
        end
    end

    always @(posedge s00_axi_aclk) begin
        if (!s00_axi_aresetn) begin
            axi_wready <= 1'b0;
        end else if (!axi_wready && s00_axi_wvalid && s00_axi_awvalid && aw_en) begin
            axi_wready <= 1'b1;
        end else begin
            axi_wready <= 1'b0;
        end
    end

    assign slv_reg_wren = axi_wready && s00_axi_wvalid && axi_awready && s00_axi_awvalid;

    always @(posedge s00_axi_aclk) begin
        if (!s00_axi_aresetn) begin
            dc_reg <= 1'b0;
            cs_n_reg <= 1'b1;
            res_n_reg <= 1'b1;
            tx_data_reg <= 8'h00;
            clk_div_reg <= 16'd5;
            start_pulse <= 1'b0;
        end else begin
            start_pulse <= 1'b0;
            if (slv_reg_wren) begin
                case (axi_awaddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB])
                    3'h0: begin
                        if (s00_axi_wstrb[0]) begin
                            start_pulse <= s00_axi_wdata[0];
                            dc_reg <= s00_axi_wdata[1];
                            cs_n_reg <= s00_axi_wdata[2];
                            res_n_reg <= s00_axi_wdata[3];
                        end
                    end
                    3'h1: begin
                        for (byte_index = 0; byte_index <= (C_S00_AXI_DATA_WIDTH/8)-1; byte_index = byte_index + 1) begin
                            if (s00_axi_wstrb[byte_index]) begin
                                if (byte_index == 0) begin
                                    tx_data_reg <= s00_axi_wdata[7:0];
                                end
                            end
                        end
                    end
                    3'h2: begin
                        if (s00_axi_wstrb[0] || s00_axi_wstrb[1]) begin
                            if (s00_axi_wdata[15:0] < 16'd2) begin
                                clk_div_reg <= 16'd2;
                            end else begin
                                clk_div_reg <= s00_axi_wdata[15:0];
                            end
                        end
                    end
                    default: begin
                    end
                endcase
            end
        end
    end

    always @(posedge s00_axi_aclk) begin
        if (!s00_axi_aresetn) begin
            axi_bvalid <= 1'b0;
            axi_bresp <= 2'b00;
        end else begin
            if (axi_awready && s00_axi_awvalid && !axi_bvalid && axi_wready && s00_axi_wvalid) begin
                axi_bvalid <= 1'b1;
                axi_bresp <= 2'b00;
            end else if (s00_axi_bready && axi_bvalid) begin
                axi_bvalid <= 1'b0;
            end
        end
    end

    always @(posedge s00_axi_aclk) begin
        if (!s00_axi_aresetn) begin
            axi_arready <= 1'b0;
            axi_araddr <= {C_S00_AXI_ADDR_WIDTH{1'b0}};
        end else if (!axi_arready && s00_axi_arvalid) begin
            axi_arready <= 1'b1;
            axi_araddr <= s00_axi_araddr;
        end else begin
            axi_arready <= 1'b0;
        end
    end

    always @(posedge s00_axi_aclk) begin
        if (!s00_axi_aresetn) begin
            axi_rvalid <= 1'b0;
            axi_rresp <= 2'b00;
        end else begin
            if (axi_arready && s00_axi_arvalid && !axi_rvalid) begin
                axi_rvalid <= 1'b1;
                axi_rresp <= 2'b00;
            end else if (axi_rvalid && s00_axi_rready) begin
                axi_rvalid <= 1'b0;
            end
        end
    end

    assign slv_reg_rden = axi_arready & s00_axi_arvalid & ~axi_rvalid;

    always @(*) begin
        case (axi_araddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB])
            3'h0: reg_data_out = {28'd0, res_n_reg, cs_n_reg, dc_reg, 1'b0};
            3'h1: reg_data_out = {24'd0, tx_data_reg};
            3'h2: reg_data_out = {16'd0, clk_div_reg};
            3'h3: reg_data_out = {30'd0, done_toggle_reg, busy_reg};
            default: reg_data_out = {C_S00_AXI_DATA_WIDTH{1'b0}};
        endcase
    end

    always @(posedge s00_axi_aclk) begin
        if (!s00_axi_aresetn) begin
            axi_rdata <= {C_S00_AXI_DATA_WIDTH{1'b0}};
        end else if (slv_reg_rden) begin
            axi_rdata <= reg_data_out;
        end
    end

    always @(posedge s00_axi_aclk) begin
        if (!s00_axi_aresetn) begin
            busy_reg <= 1'b0;
            done_toggle_reg <= 1'b0;
            sclk_reg <= 1'b0;
            sda_reg <= 1'b0;
            shift_reg <= 8'h00;
            bit_idx <= 3'd7;
            div_cnt <= 16'd0;
            phase_reg <= 1'b0;
        end else begin
            if (!busy_reg) begin
                sclk_reg <= 1'b0;
                div_cnt <= 16'd0;
                phase_reg <= 1'b0;
                if (start_pulse) begin
                    busy_reg <= 1'b1;
                    shift_reg <= tx_data_reg;
                    bit_idx <= 3'd7;
                    sda_reg <= tx_data_reg[7];
                end
            end else begin
                if (div_cnt >= (clk_div_reg - 1'b1)) begin
                    div_cnt <= 16'd0;
                    if (!phase_reg) begin
                        sclk_reg <= 1'b1;
                        phase_reg <= 1'b1;
                    end else begin
                        sclk_reg <= 1'b0;
                        phase_reg <= 1'b0;
                        if (bit_idx == 3'd0) begin
                            busy_reg <= 1'b0;
                            done_toggle_reg <= ~done_toggle_reg;
                            sda_reg <= 1'b0;
                        end else begin
                            bit_idx <= bit_idx - 1'b1;
                            sda_reg <= shift_reg[bit_idx - 1'b1];
                        end
                    end
                end else begin
                    div_cnt <= div_cnt + 1'b1;
                end
            end
        end
    end

endmodule
