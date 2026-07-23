`timescale 1ns/1ps

module test_mips_tb;

    // 1. 信号声明
    reg clk;
    reg rst;

    // 2. 实例化顶层 MIPS 模块
    mips my_mips (
        .clk(clk),
        .rst(rst)
    );

    // 3. 时钟生成（10ns周期）
    initial clk = 0;
    always #5 clk = ~clk;

    // 4. 初始化与运行控制
    initial begin
        $display("\n------ MIPS CPU Run-to-Completion Test Start ------");

        // 复位处理器
        rst = 1;
        #20; // 保持复位20ns
        rst = 0;
        $display("Reset released. Processor running...");

        // 运行一个足够长的固定时间，以确保程序跑完
        // 这个时间需要比你最长的测试程序执行时间还要长
        #2000;

        // 5. 打印最终寄存器快照
        $display("\n-----------------------------------------------------");
        $display("------ Processor Final State Snapshot at %0t ns ------", $time);
        $display("-----------------------------------------------------");

        // 打印 $s0 - $s7 寄存器
        $display("s0-s7: 0x%08h, 0x%08h, 0x%08h, 0x%08h, 0x%08h, 0x%08h, 0x%08h, 0x%08h",
                 my_mips.datapath_unit.gpr_unit.registers[16],
                 my_mips.datapath_unit.gpr_unit.registers[17],
                 my_mips.datapath_unit.gpr_unit.registers[18],
                 my_mips.datapath_unit.gpr_unit.registers[19],
                 my_mips.datapath_unit.gpr_unit.registers[20],
                 my_mips.datapath_unit.gpr_unit.registers[21],
                 my_mips.datapath_unit.gpr_unit.registers[22],
                 my_mips.datapath_unit.gpr_unit.registers[23]);

        // 打印 $t0 - $t9 寄存器
        $display("t0-t7: 0x%08h, 0x%08h, 0x%08h, 0x%08h, 0x%08h, 0x%08h, 0x%08h, 0x%08h",
                 my_mips.datapath_unit.gpr_unit.registers[8],
                 my_mips.datapath_unit.gpr_unit.registers[9],
                 my_mips.datapath_unit.gpr_unit.registers[10],
                 my_mips.datapath_unit.gpr_unit.registers[11],
                 my_mips.datapath_unit.gpr_unit.registers[12],
                 my_mips.datapath_unit.gpr_unit.registers[13],
                 my_mips.datapath_unit.gpr_unit.registers[14],
                 my_mips.datapath_unit.gpr_unit.registers[15]);
        $display("t8-t9: 0x%08h, 0x%08h",
                 my_mips.datapath_unit.gpr_unit.registers[24],
                 my_mips.datapath_unit.gpr_unit.registers[25]);

        // 打印特殊寄存器
        $display("v0 (ret val) : 0x%08h", my_mips.datapath_unit.gpr_unit.registers[2]);
        $display("ra (ret addr): 0x%08h", my_mips.datapath_unit.gpr_unit.registers[31]);
        $display("-----------------------------------------------------");

        $display("\n------ MIPS CPU Test End ------");
        $finish; // 自动结束仿真
    end

endmodule