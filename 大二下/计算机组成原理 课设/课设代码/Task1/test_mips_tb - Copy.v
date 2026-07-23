`timescale 1ns / 1ps

module test_mips_tb;

    // 1. 信号声明
    reg clk;
    reg rst;

    // 2. 实例化你的完整 MIPS 处理器
    mips mips_cpu_uut (
        .clk(clk),
        .rst(rst)
    );

    // 3. 时钟生成
    initial clk = 0;
    always #5 clk = ~clk; // 周期10ns

    // 4. 测试序列
    initial begin
        $display("\n------ MIPS CPU Final Program Execution Start ------");

        // 复位处理器
        rst = 1;
        #15; // 保持复位
        rst = 0;
        $display("Reset released. Processor starts executing final program...");

        // 让处理器自由运行足够长的时间以确保程序能进入最终的停机循环
        #5000;

        // 5. 最终状态报告
        $display("\n-----------------------------------------------------");
        $display("------ Processor Final State Snapshot ------");
        $display("-----------------------------------------------------");
        
        // 打印 $s0 - $s7 寄存器
        $display("s0-s7: 0x%h, 0x%h, 0x%h, 0x%h, 0x%h, 0x%h, 0x%h, 0x%h",
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[16],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[17],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[18],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[19],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[20],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[21],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[22],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[23]);

        // 打印 $t0 - $t9 寄存器
        $display("t0-t7: 0x%h, 0x%h, 0x%h, 0x%h, 0x%h, 0x%h, 0x%h, 0x%h",
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[8],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[9],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[10],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[11],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[12],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[13],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[14],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[15]);
        $display("t8-t9: 0x%h, 0x%h",
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[24],
                  mips_cpu_uut.datapath_unit.gpr_unit.registers[25]);

        // 打印特殊寄存器
        $display("v0 (ret val) : 0x%h", mips_cpu_uut.datapath_unit.gpr_unit.registers[2]);
        $display("ra (ret addr): 0x%h", mips_cpu_uut.datapath_unit.gpr_unit.registers[31]);
        $display("-----------------------------------------------------");

        $display("\n------ MIPS CPU Final Program Execution End ------");
        $finish;
    end

    // 6. 逐指令实时监控器
    integer cycle_count = 0;
    always @(posedge clk) begin
        if (rst == 0 && cycle_count < 200) begin // 只监控前200个周期防止刷屏
            cycle_count = cycle_count + 1;
            $display("--- Cycle %0d --- PC: 0x%h, Instr: 0x%h", 
                      cycle_count, 
                      mips_cpu_uut.datapath_unit.pc_out, 
                      mips_cpu_uut.w_instr);
            if (mips_cpu_uut.w_reg_write) begin
                $display("  \\-> GPR Write to $%d with Data 0x%h", 
                          mips_cpu_uut.datapath_unit.gpr_write_addr, 
                          mips_cpu_uut.datapath_unit.gpr_write_data);
            end
        end
    end

endmodule