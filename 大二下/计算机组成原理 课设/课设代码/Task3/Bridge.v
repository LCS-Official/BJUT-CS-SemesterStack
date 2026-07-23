// 使用内存映射，让I/O也能被CPU访问
module Bridge(praddr, prwd, prrd, dev0_rd, dev1_rd, dev2_rd, dev_wd, dev_addr, wen, dev0_we, dev2_we, hwint, irq);
	input [31:0] praddr, prwd;							// praddr: CPU要访问的外设地址; prwd: CPU要写入的数据
	input [31:0] dev0_rd, dev1_rd, dev2_rd;		// devX_rd: 分别从设备0, 1, 2读出的数据
	input wen, irq;										// wen: CPU发出的通用写使能信号 (对应sw, sb等指令)
																// irq: 来自某个设备的中断请求信号 (如Timer)
																
	output [31:0] prrd;									// prrd: 读取到的外设数据，送回给CPU
	output [31:0] dev_wd, dev_addr;					// dev_wd/addr: 将CPU的写数据和地址广播给所有外设
	output dev0_we, dev2_we; 							// devX_we: 发往特定设备的专用写使能信号
	output [5:0] hwint;									// hwint: 格式化后的硬件中断向量，送往CP0
  
    // --- 地址译码逻辑 ---
    // 地址命中信号，用于判断CPU当前访问的地址是否属于某个特定外设
    wire hitdev0, hitdev1, hitdev2;
 
// 特定地址->特定设备，内存映射 

    // 当地址为0x7f00, 0x7f04, 0x7f08之一时，命中设备0 (例如：Timer的CTRL, PRESET, COUNT寄存器)
    assign hitdev0 = (praddr == 32'h0000_7f00) || (praddr == 32'h0000_7f04) || (praddr == 32'h0000_7f08);
    // 当地址为0x7f0c时，命中设备1
    assign hitdev1 = (praddr == 32'h0000_7f0c);
    // 当地址为0x7f10或0x7f14时，命中设备2
    assign hitdev2 = (praddr == 32'h0000_7f10) || (praddr == 32'h0000_7f14);
    
// 确定了目标设备后，Bridge需要精确地引导数据的流向
    // --- 写操作路由逻辑 ---
    // 当命中设备0且CPU的通用写使能有效时，才产生对设备0的专用写使能信号
	 // 专用的写使能信号，确保只有特定设备接受
    assign dev0_we = hitdev0 & wen;
    // 同理，产生对设备2的专用写使能信号
    assign dev2_we = hitdev2 & wen;
    // 注意：此设计中设备1似乎是只读的，没有为它生成写使能信号

    
    // --- 读操作路由逻辑 (一个多路选择器) ---
	 // 数据总线一次只能传输一个设备的数据，于是需要选择
    // 根据命中的设备，选择对应设备的数据作为读总线(prrd)的返回数据
    assign prrd =   hitdev0 ? dev0_rd :       // 如果命中设备0，则prrd等于dev0_rd
                    hitdev1 ? dev1_rd :       // 否则，如果命中设备1，则prrd等于dev1_rd
                    hitdev2 ? dev2_rd :       // 否则，如果命中设备2，则prrd等于dev2_rd
                    32'bz;                    // 否则 (没有命中任何设备)，总线处于高阻态
    
    // --- 数据和地址广播 ---
	 // CPU的中断控制器（CP0）需要知道是具体哪个设备触发了中断
    assign dev_wd = prwd;
    assign dev_addr = praddr;
    
    // --- 中断处理逻辑 ---
    // 对中断信号进行格式化、传递
	 // 有多个中断源，Bridge就会负责将它们映射到hwint的不同位上
    assign hwint = {5'b0, irq};

endmodule
  