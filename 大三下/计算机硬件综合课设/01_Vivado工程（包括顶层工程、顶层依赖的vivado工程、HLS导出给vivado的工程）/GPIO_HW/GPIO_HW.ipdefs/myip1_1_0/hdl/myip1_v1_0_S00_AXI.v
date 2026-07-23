`timescale 1 ns / 1 ps

module myip1_v1_0_S00_AXI #
(
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 4
)
(
    // AXI4-Lite 端口
    input wire  S_AXI_ACLK,
    input wire  S_AXI_ARESETN,
    input wire [C_S_AXI_ADDR_WIDTH-1 : 0] S_AXI_AWADDR,
    input wire [2 : 0] S_AXI_AWPROT,
    input wire  S_AXI_AWVALID,
    output wire  S_AXI_AWREADY,
    input wire [C_S_AXI_DATA_WIDTH-1 : 0] S_AXI_WDATA,
    input wire [(C_S_AXI_DATA_WIDTH/8)-1 : 0] S_AXI_WSTRB,
    input wire  S_AXI_WVALID,
    output wire  S_AXI_WREADY,
    output wire [1 : 0] S_AXI_BRESP,
    output wire  S_AXI_BVALID,
    input wire  S_AXI_BREADY,
    input wire [C_S_AXI_ADDR_WIDTH-1 : 0] S_AXI_ARADDR,
    input wire [2 : 0] S_AXI_ARPROT,
    input wire  S_AXI_ARVALID,
    output wire  S_AXI_ARREADY,
    output wire [C_S_AXI_DATA_WIDTH-1 : 0] S_AXI_RDATA,
    output wire [1 : 0] S_AXI_RRESP,
    output wire  S_AXI_RVALID,
    input wire  S_AXI_RREADY,
    // 用户输出端口：LED 控制
    output wire led_r,
    output wire led_g
);

// ============================================================
// AXI4-Lite 从机协议实现（标准模板，保持不变）
// ============================================================
reg [C_S_AXI_ADDR_WIDTH-1 : 0]  axi_awaddr;
reg  axi_awready;
reg  axi_wready;
reg [1 : 0]  axi_bresp;
reg  axi_bvalid;
reg [C_S_AXI_ADDR_WIDTH-1 : 0]  axi_araddr;
reg  axi_arready;
reg [C_S_AXI_DATA_WIDTH-1 : 0]  axi_rdata;
reg [1 : 0]  axi_rresp;
reg  axi_rvalid;
localparam integer ADDR_LSB = (C_S_AXI_DATA_WIDTH/32) + 1;
localparam integer OPT_MEM_ADDR_BITS = 1;
reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg0, slv_reg1, slv_reg2, slv_reg3;
wire slv_reg_rden;
wire slv_reg_wren;
reg [C_S_AXI_DATA_WIDTH-1:0] reg_data_out;
integer byte_index;
reg aw_en;

assign S_AXI_AWREADY = axi_awready;
assign S_AXI_WREADY   = axi_wready;
assign S_AXI_BRESP    = axi_bresp;
assign S_AXI_BVALID   = axi_bvalid;
assign S_AXI_ARREADY  = axi_arready;
assign S_AXI_RDATA    = axi_rdata;
assign S_AXI_RRESP    = axi_rresp;
assign S_AXI_RVALID   = axi_rvalid;

// AXI 写地址就绪
always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
        axi_awready <= 1'b0;
        aw_en <= 1'b1;
    end else begin
        if (~axi_awready && S_AXI_AWVALID && S_AXI_WVALID && aw_en) begin
            axi_awready <= 1'b1;
            aw_en <= 1'b0;
        end else if (S_AXI_BREADY && axi_bvalid) begin
            aw_en <= 1'b1;
            axi_awready <= 1'b0;
        end else begin
            axi_awready <= 1'b0;
        end
    end
end

// AXI 写地址锁存
always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
        axi_awaddr <= 0;
    end else begin
        if (~axi_awready && S_AXI_AWVALID && S_AXI_WVALID && aw_en) begin
            axi_awaddr <= S_AXI_AWADDR;
        end
    end
end

// AXI 写数据就绪
always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
        axi_wready <= 1'b0;
    end else begin
        if (~axi_wready && S_AXI_WVALID && S_AXI_AWVALID && aw_en) begin
            axi_wready <= 1'b1;
        end else begin
            axi_wready <= 1'b0;
        end
    end
end

// 写寄存器使能
assign slv_reg_wren = axi_wready && S_AXI_WVALID && axi_awready && S_AXI_AWVALID;

// 写寄存器逻辑（保留原样，供软件读写）
always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
        slv_reg0 <= 0;
        slv_reg1 <= 0;
        slv_reg2 <= 0;
        slv_reg3 <= 0;
    end else begin
        if (slv_reg_wren) begin
            case ( axi_awaddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB] )
                2'h0: for (byte_index = 0; byte_index <= (C_S_AXI_DATA_WIDTH/8)-1; byte_index = byte_index+1)
                        if (S_AXI_WSTRB[byte_index]) slv_reg0[(byte_index*8)+:8] <= S_AXI_WDATA[(byte_index*8)+:8];
                2'h1: for (byte_index = 0; byte_index <= (C_S_AXI_DATA_WIDTH/8)-1; byte_index = byte_index+1)
                        if (S_AXI_WSTRB[byte_index]) slv_reg1[(byte_index*8)+:8] <= S_AXI_WDATA[(byte_index*8)+:8];
                2'h2: for (byte_index = 0; byte_index <= (C_S_AXI_DATA_WIDTH/8)-1; byte_index = byte_index+1)
                        if (S_AXI_WSTRB[byte_index]) slv_reg2[(byte_index*8)+:8] <= S_AXI_WDATA[(byte_index*8)+:8];
                2'h3: for (byte_index = 0; byte_index <= (C_S_AXI_DATA_WIDTH/8)-1; byte_index = byte_index+1)
                        if (S_AXI_WSTRB[byte_index]) slv_reg3[(byte_index*8)+:8] <= S_AXI_WDATA[(byte_index*8)+:8];
                default: ;
            endcase
        end
    end
end

// 写响应
always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
        axi_bvalid <= 0;
        axi_bresp  <= 2'b0;
    end else begin
        if (axi_awready && S_AXI_AWVALID && ~axi_bvalid && axi_wready && S_AXI_WVALID) begin
            axi_bvalid <= 1'b1;
            axi_bresp  <= 2'b0;
        end else if (S_AXI_BREADY && axi_bvalid) begin
            axi_bvalid <= 1'b0;
        end
    end
end

// AXI 读地址就绪
always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
        axi_arready <= 1'b0;
        axi_araddr  <= 32'b0;
    end else begin
        if (~axi_arready && S_AXI_ARVALID) begin
            axi_arready <= 1'b1;
            axi_araddr  <= S_AXI_ARADDR;
        end else begin
            axi_arready <= 1'b0;
        end
    end
end

// 读数据有效
always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
        axi_rvalid <= 0;
        axi_rresp  <= 0;
    end else begin
        if (axi_arready && S_AXI_ARVALID && ~axi_rvalid) begin
            axi_rvalid <= 1'b1;
            axi_rresp  <= 2'b0;
        end else if (axi_rvalid && S_AXI_RREADY) begin
            axi_rvalid <= 1'b0;
        end
    end
end

// 读数据组合逻辑（寄存器读回，用于调试，但无外部输出）
assign slv_reg_rden = axi_arready & S_AXI_ARVALID & ~axi_rvalid;
always @(*) begin
    case ( axi_araddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB] )
        2'h0   : reg_data_out <= slv_reg0;
        2'h1   : reg_data_out <= slv_reg1;
        2'h2   : reg_data_out <= slv_reg2;
        2'h3   : reg_data_out <= slv_reg3;
        default : reg_data_out <= 0;
    endcase
end

always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
        axi_rdata <= 0;
    end else begin
        if (slv_reg_rden) begin
            axi_rdata <= reg_data_out;
        end
    end
end

// ============================================================
// 用户逻辑：触发脉冲生成 + warning_light 实例化
// ============================================================
// 检测写寄存器0（地址偏移0x00）且写入数据bit0=1，产生单周期脉冲
reg wr0_req, wr0_req_d1;
wire wr0_pulse;

always @(posedge S_AXI_ACLK or negedge S_AXI_ARESETN) begin
    if (!S_AXI_ARESETN) begin
        wr0_req    <= 1'b0;
        wr0_req_d1 <= 1'b0;
    end else begin
        // 锁存写请求：有效写传输 + 地址匹配寄存器0 + 写入数据bit0为1
        wr0_req <= slv_reg_wren && (axi_awaddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB] == 2'h0) && S_AXI_WDATA[0];
        wr0_req_d1 <= wr0_req;
    end
end
assign wr0_pulse = wr0_req && !wr0_req_d1;

// 实例化 warning_light（原模块未修改，去掉调试输出连接）
warning_light u_warning_light (
    .clk   (S_AXI_ACLK),
    .rst_n (S_AXI_ARESETN),
    .alert (wr0_pulse),
    .led_r (led_r),
    .led_g (led_g),
    .dbg_state(),   // 悬空
    .dbg_cnt()      // 悬空
);

endmodule