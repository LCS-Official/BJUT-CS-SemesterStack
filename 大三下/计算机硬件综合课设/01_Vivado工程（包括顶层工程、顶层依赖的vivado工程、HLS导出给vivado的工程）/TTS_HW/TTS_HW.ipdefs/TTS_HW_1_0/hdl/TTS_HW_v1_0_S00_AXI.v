`timescale 1 ns / 1 ps

module TTS_HW_v1_0_S00_AXI #
(
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 4
)
(
    output wire  tx,
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
    input wire  S_AXI_RREADY
);

    // AXI4LITE signals
    reg [C_S_AXI_ADDR_WIDTH-1 : 0]    axi_awaddr;
    reg       axi_awready;
    reg       axi_wready;
    reg [1 : 0]   axi_bresp;
    reg       axi_bvalid;
    reg [C_S_AXI_ADDR_WIDTH-1 : 0]    axi_araddr;
    reg       axi_arready;
    reg [C_S_AXI_DATA_WIDTH-1 : 0]    axi_rdata;
    reg [1 : 0]   axi_rresp;
    reg       axi_rvalid;

    localparam integer ADDR_LSB = (C_S_AXI_DATA_WIDTH/32) + 1;
    localparam integer OPT_MEM_ADDR_BITS = 1;

    reg [C_S_AXI_DATA_WIDTH-1:0]  slv_reg0;
    reg [C_S_AXI_DATA_WIDTH-1:0]  slv_reg1;
    reg [C_S_AXI_DATA_WIDTH-1:0]  slv_reg2;
    reg [C_S_AXI_DATA_WIDTH-1:0]  slv_reg3;
    wire       slv_reg_rden;
    wire       slv_reg_wren;
    reg [C_S_AXI_DATA_WIDTH-1:0]   reg_data_out;
    integer    byte_index;
    reg        aw_en;

    assign S_AXI_AWREADY = axi_awready;
    assign S_AXI_WREADY  = axi_wready;
    assign S_AXI_BRESP   = axi_bresp;
    assign S_AXI_BVALID  = axi_bvalid;
    assign S_AXI_ARREADY = axi_arready;
    assign S_AXI_RDATA   = axi_rdata;
    assign S_AXI_RRESP   = axi_rresp;
    assign S_AXI_RVALID  = axi_rvalid;

    // axi_awready generation
    always @( posedge S_AXI_ACLK ) begin
        if ( S_AXI_ARESETN == 1'b0 ) begin
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

    // axi_awaddr latching
    always @( posedge S_AXI_ACLK ) begin
        if ( S_AXI_ARESETN == 1'b0 ) begin
            axi_awaddr <= 0;
        end else begin    
            if (~axi_awready && S_AXI_AWVALID && S_AXI_WVALID && aw_en) begin
                axi_awaddr <= S_AXI_AWADDR;
            end
        end 
    end       

    // axi_wready generation
    always @( posedge S_AXI_ACLK ) begin
        if ( S_AXI_ARESETN == 1'b0 ) begin
            axi_wready <= 1'b0;
        end else begin    
            if (~axi_wready && S_AXI_WVALID && S_AXI_AWVALID && aw_en) begin
                axi_wready <= 1'b1;
            end else begin
                axi_wready <= 1'b0;
            end
        end 
    end       

    assign slv_reg_wren = axi_wready && S_AXI_WVALID && axi_awready && S_AXI_AWVALID;

    // 用户逻辑：产生 start_pulse
    reg start_pulse;

    always @( posedge S_AXI_ACLK ) begin
        if ( S_AXI_ARESETN == 1'b0 ) begin
            slv_reg0 <= 0;
            slv_reg1 <= 0;
            slv_reg2 <= 0;
            slv_reg3 <= 0;
            start_pulse <= 1'b0;
        end else begin
            if (slv_reg_wren) begin
                case ( axi_awaddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB] )
                    2'h0:
                        for ( byte_index = 0; byte_index <= (C_S_AXI_DATA_WIDTH/8)-1; byte_index = byte_index+1 )
                            if ( S_AXI_WSTRB[byte_index] == 1 )
                                slv_reg0[(byte_index*8) +: 8] <= S_AXI_WDATA[(byte_index*8) +: 8];
                    2'h1:
                        for ( byte_index = 0; byte_index <= (C_S_AXI_DATA_WIDTH/8)-1; byte_index = byte_index+1 )
                            if ( S_AXI_WSTRB[byte_index] == 1 )
                                slv_reg1[(byte_index*8) +: 8] <= S_AXI_WDATA[(byte_index*8) +: 8];
                    2'h2:
                        for ( byte_index = 0; byte_index <= (C_S_AXI_DATA_WIDTH/8)-1; byte_index = byte_index+1 )
                            if ( S_AXI_WSTRB[byte_index] == 1 )
                                slv_reg2[(byte_index*8) +: 8] <= S_AXI_WDATA[(byte_index*8) +: 8];
                    2'h3:
                        for ( byte_index = 0; byte_index <= (C_S_AXI_DATA_WIDTH/8)-1; byte_index = byte_index+1 )
                            if ( S_AXI_WSTRB[byte_index] == 1 )
                                slv_reg3[(byte_index*8) +: 8] <= S_AXI_WDATA[(byte_index*8) +: 8];
                    default: ;
                endcase
                if ( axi_awaddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB] == 2'h0 )
                    start_pulse <= 1'b1;
                else
                    start_pulse <= 1'b0;
            end else begin
                start_pulse <= 1'b0;
            end
        end
    end

    // 写响应
    always @( posedge S_AXI_ACLK ) begin
        if ( S_AXI_ARESETN == 1'b0 ) begin
            axi_bvalid  <= 0;
            axi_bresp   <= 2'b0;
        end else begin    
            if (axi_awready && S_AXI_AWVALID && ~axi_bvalid && axi_wready && S_AXI_WVALID) begin
                axi_bvalid <= 1'b1;
                axi_bresp  <= 2'b0;
            end else begin
                if (S_AXI_BREADY && axi_bvalid) 
                    axi_bvalid <= 1'b0; 
            end
        end
    end   

    // 读地址
    always @( posedge S_AXI_ACLK ) begin
        if ( S_AXI_ARESETN == 1'b0 ) begin
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
    always @( posedge S_AXI_ACLK ) begin
        if ( S_AXI_ARESETN == 1'b0 ) begin
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

    always @( posedge S_AXI_ACLK ) begin
        if ( S_AXI_ARESETN == 1'b0 ) begin
            axi_rdata  <= 0;
        end else begin    
            if (slv_reg_rden)
                axi_rdata <= reg_data_out;
        end
    end    

    // ==================== 实例化 tts_controller ====================
    tts_controller u_tts_controller (
        .clk   ( S_AXI_ACLK ),
        .rst_n ( S_AXI_ARESETN ),
        .start ( start_pulse ),
        .tx    ( tx ),
        .dbg_state     (),
        .dbg_byte_index(),
        .dbg_start_pedge(),
        .dbg_baud_cnt  (),
        .dbg_bit_cnt   ()
    );

endmodule

// ==================== tts_controller 模块定义（内嵌） ====================
`timescale 1ns / 1ps

module tts_controller (
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    output reg  tx,
    output wire [2:0] dbg_state,
    output wire [4:0] dbg_byte_index,
    output wire       dbg_start_pedge,
    output wire [13:0] dbg_baud_cnt,
    output wire [3:0] dbg_bit_cnt
);

    // 消息内容 "检测到用户疲劳" (GB2312)
    localparam MSG_LEN = 14;
    reg [4:0] byte_index;   // 0~13
    wire [7:0] msg_data;
    assign msg_data =
        (byte_index ==  0) ? 8'hBC :   // 检 高
        (byte_index ==  1) ? 8'hEC :   // 检 低
        (byte_index ==  2) ? 8'hB2 :   // 测 高
        (byte_index ==  3) ? 8'hE2 :   // 测 低
        (byte_index ==  4) ? 8'hB5 :   // 到 高
        (byte_index ==  5) ? 8'hBD :   // 到 低
        (byte_index == 6) ? 8'hD3 :   // 用 高
        (byte_index == 7) ? 8'hC3 :   // 用 低
        (byte_index == 8) ? 8'hBB :   // 户 高
        (byte_index == 9) ? 8'hA7 :   // 户 低
        (byte_index == 10) ? 8'hC6 :   // 疲 高
        (byte_index == 11) ? 8'hA3 :   // 疲 低
        (byte_index == 12) ? 8'hC0 :   // 劳 高
        (byte_index == 13) ? 8'hCD :   // 劳 低
        8'h00;

    // UART 参数 (125MHz 时钟，9600 波特率)
    localparam BAUD_CNT_MAX = 13020;
    reg [13:0] baud_cnt;
    reg [3:0]  bit_cnt;
    reg [7:0]  tx_shift;

    assign dbg_baud_cnt = baud_cnt;
    assign dbg_bit_cnt = bit_cnt;

    // start 上升沿检测
    reg start_sync, start_d1;
    wire start_posedge;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            start_sync <= 0;
            start_d1   <= 0;
        end else begin
            start_sync <= start;
            start_d1   <= start_sync;
        end
    end
    assign start_posedge = start_sync && !start_d1;

    // 状态机
    localparam IDLE      = 3'd0;
    localparam LOAD_BYTE = 3'd1;
    localparam TX_START  = 3'd2;
    localparam TX_DATA   = 3'd3;
    localparam TX_STOP   = 3'd4;

    reg [2:0] state, next_state;

    // 时序逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= IDLE;
            baud_cnt   <= 0;
            bit_cnt    <= 0;
            byte_index <= 0;
            tx_shift   <= 0;
            tx         <= 1'b1;
        end else begin
            state <= next_state;
            case (state)
                IDLE: begin
                    tx         <= 1'b1;
                    baud_cnt   <= 0;
                    bit_cnt    <= 0;
                    byte_index <= 0;
                end
                LOAD_BYTE: begin
                    tx_shift   <= msg_data;
                    baud_cnt   <= 0;
                    bit_cnt    <= 0;
                    tx         <= 1'b1;
                end
                TX_START: begin
                    tx <= 1'b0;
                    if (baud_cnt == BAUD_CNT_MAX)
                        baud_cnt <= 0;
                    else
                        baud_cnt <= baud_cnt + 1;
                end
                TX_DATA: begin
                    tx <= tx_shift[bit_cnt];
                    if (baud_cnt == BAUD_CNT_MAX) begin
                        baud_cnt <= 0;
                        if (bit_cnt == 7)
                            bit_cnt <= 0;
                        else
                            bit_cnt <= bit_cnt + 1;
                    end else begin
                        baud_cnt <= baud_cnt + 1;
                    end
                end
                TX_STOP: begin
                    tx <= 1'b1;
                    if (baud_cnt == BAUD_CNT_MAX) begin
                        baud_cnt <= 0;
                        if (byte_index == (MSG_LEN - 1))
                            byte_index <= 0;
                        else
                            byte_index <= byte_index + 1;
                    end else begin
                        baud_cnt <= baud_cnt + 1;
                    end
                end
                default: baud_cnt <= 0;
            endcase
        end
    end

    // 组合逻辑：下一状态
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: if (start_posedge) next_state = LOAD_BYTE;
            LOAD_BYTE: next_state = TX_START;
            TX_START: if (baud_cnt == BAUD_CNT_MAX) next_state = TX_DATA;
            TX_DATA: if (baud_cnt == BAUD_CNT_MAX && bit_cnt == 7) next_state = TX_STOP;
            TX_STOP: if (baud_cnt == BAUD_CNT_MAX) begin
                if (byte_index == (MSG_LEN - 1)) next_state = IDLE;
                else next_state = LOAD_BYTE;
            end
            default: next_state = IDLE;
        endcase
    end

    // 调试输出
    assign dbg_state       = state;
    assign dbg_byte_index  = byte_index;
    assign dbg_start_pedge = start_posedge;

endmodule