module bridge(praddr, bridgedin, cpu_rd, dev0_rd, dev1_rd, dev2_rd, 
            dev_wd, dev_addr, devwr, dev0_we, dev2_we, hwint, irq, change, chan);

    input [31:0] praddr;// 31位地址总线 mips处理器输出的
    input [31:0] bridgedin;// 要写入的数据
    input [31:0]dev0_rd, dev1_rd, dev2_rd;// 3个设备的readdata
    input devwr;// 允许写入cp0
    input irq;// timer给的中断请求
    input chan;
	 
    output [31:0] cpu_rd;// 写入cpu的数据
    output [31:0] dev_wd;// 要存入设备的数据 
    output [3:0] dev_addr;// 要存入设备的地址
    output dev0_we, dev2_we;// timer 和 output的写允许信号

    output [5:0] hwint;// 6个硬件中断请求

    output change;

    assign change = chan; // 作为controller和定时器的变量“桥”
    
    wire hitdev0, hitdev1, hitdev2;
    
    // ！！！！！设备地址译码！！！！！！
    /*
        设备0：timer：控制reg 0x0000_7F00、初值reg：0x0000_7F04、计数reg：0x0000_7F08
        设备1：输入：0x0000_7F10为switch
        设备2：输出：0x0000_7F20与24为output_dev
    */
    // 地址选的是哪一个外设
    assign hitdev0 = ((praddr == 32'h0000_7f00) |
                    (praddr == 32'h0000_7f04) |
                    (praddr == 32'h0000_7f08)) ? 1 : 0;  
    assign hitdev1 = (praddr == 32'h0000_7f10) ? 1 : 0; //switch  
    assign hitdev2 = (praddr == 32'h0000_7f20) |
                    (praddr == 32'h0000_7f24) ? 1 : 0;   
    
    // 外设写使能，控制数据如何从CPU写入到目标设备中
    assign dev0_we = hitdev0 & devwr;
    assign dev2_we = hitdev2 & devwr;
    assign dev_wd = bridgedin;

    // 根据设备地址译码，控制着数据如何从正确的设备读取并返回给CPU
    assign cpu_rd = hitdev0 ? dev0_rd : (hitdev1 ? dev1_rd : (hitdev2 ? dev2_rd : 32'bz));
    
	 // 处理中断、辅助信息
    assign dev_addr = praddr[5:2];//00 dev0 01 dev1 10 dev2，如此存储
    assign hwint = {5'b0, irq};
endmodule
  