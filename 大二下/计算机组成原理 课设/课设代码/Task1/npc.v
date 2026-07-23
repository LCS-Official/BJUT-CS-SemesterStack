/*
 * 模块名称: npc (Next PC Calculation Unit)
 * 文件名称: npc.v
 * 描述:     根据当前PC、指令和控制信号，计算下一条指令的地址。
 * (已修改为与本项目其他模块完全匹配的版本)
 */

`include "defines.v" // 引入包含宏定义的头文件

module npc (
    // -- 项目中 datapath 所要求的标准接口 --
    input  [31:0] PC,          // 输入：当前PC值 (对应你的 addr)
    input  [31:0] SignImm,     // 输入：来自EXT模块的32位符号扩展立即数 (用于beq)
    input  [25:0] Instr_25_0,  // 输入：来自指令的低26位 (用于j, jal, 对应你的 imm)
    input  [31:0] JR_Addr,     // 输入：来自GPR的跳转地址 (用于jr, 对应你的 reg_data)
    input  [1:0]  PCSrc,       // 输入：来自控制器的2位PC源选择信号 (统一了你的 pc_sel 和 npc_sel)
    
    output reg [31:0] NPC          // 输出：计算出的下一条指令地址
);

    // 定义四个可能的NPC来源
    wire [31:0] npc_plus4;
    wire [31:0] npc_branch;
    wire [31:0] npc_jump;
    // 第四个来源是 JR_Addr 输入

    // 对应你的 pc_sel = 2'b00 的情况
    assign npc_plus4 = PC + 32'd4;

    // 对应你的 if (zero & npc_sel) 的情况, 但使用了正确的立即数输入 SignImm
    assign npc_branch = npc_plus4 + (SignImm << 2);

    // 对应你的 pc_sel = 2'b01 的情况
    assign npc_jump = {PC[31:28], Instr_25_0, 2'b00};

    // 使用 always 块和 case 语句实现一个4选1多路选择器
    // 根据控制器送来的统一的 PCSrc 信号，选择正确的NPC值
    always @(*) begin
        case (PCSrc)
            `PC_SRC_P4:    NPC = npc_plus4;    // 来源0: PC + 4 (用于顺序执行)
            `PC_SRC_BRANCH: NPC = npc_branch;   // 来源1: 分支目标 (用于beq)
            `PC_SRC_JUMP:   NPC = npc_jump;     // 来源2: 跳转目标 (用于j, jal)
            `PC_SRC_JR:     NPC = JR_Addr;      // 来源3: 寄存器跳转 (用于jr)
            default:       NPC = npc_plus4;    // 默认安全值为 PC + 4
        endcase
    end

endmodule