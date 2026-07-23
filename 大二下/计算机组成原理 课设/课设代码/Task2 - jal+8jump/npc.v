/*
 * --------------------------------------------------------------------
 * 模块名称: npc (Next PC Calculation Unit)
 * 描述:     根据当前PC、指令和控制信号，计算下一条指令的地址。
 * --------------------------------------------------------------------
 */
`include "defines.v"
module npc (
    input  [31:0] PC,           // 输入：当前PC值
    input  [31:0] SignImm,      // 输入：来自EXT模块的32位符号扩展立即数 (用于beq)
    input  [25:0] Instr_25_0,   // 输入：来自指令的低26位 (用于j, jal)
    input  [31:0] JR_Addr,      // 输入：来自GPR的跳转地址 (用于jr)
    input  [1:0]  PCSrc,        // 输入：来自控制器的PC源选择信号
    output reg [31:0] NPC         // 输出：计算出的下一条指令地址
);
    wire [31:0] npc_plus4;
    wire [31:0] npc_branch;
    wire [31:0] npc_jump;

    assign npc_plus4 = PC + 32'd4;
    assign npc_branch = npc_plus4 + (SignImm << 2);
    assign npc_jump = {PC[31:28], Instr_25_0, 2'b00};

    always @(*) begin
        case (PCSrc)
            `PC_SRC_ALU:     NPC = npc_plus4;
            `PC_SRC_BRANCH: NPC = npc_branch;
            `PC_SRC_JUMP:   NPC = npc_jump;
            `PC_SRC_JR:     NPC = JR_Addr;
            default:        NPC = npc_plus4; // 默认安全值
        endcase
    end
endmodule
