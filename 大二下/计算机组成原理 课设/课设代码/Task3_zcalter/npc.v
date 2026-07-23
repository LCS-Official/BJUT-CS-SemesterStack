module npc(
  input [31:0] pcin,//输入的pc
  input [31:0] rd1,//jr 跳转的寄存器中地址
  input [1:0] npcop,//00 pc4 01 beq 10 jal 11 jr
  input zero,
  input [25:0] imm,//指令低26位 j指令
  output reg [31:0] nextpc,
  output [31:0] pc_4,//jal要存入pc+4到寄存器中 返回地址
  input rst,//是否结果是0 beq 共同决定是否跳转
  input IntPc, //中断请求信号 跳转到中断执行地址 s10状态且中断请求信号
  input [31:0] epc,
  input eret
 );
  
  
	wire [15:0] imm16;//从26位中取低16位 beq
	wire [31:0] temp, extout, j_addr;
	reg [31:0] pcnew;

	assign pc_4 = pcin;
	assign imm16 = imm[15:0];
	assign temp = {{16{imm16[15]}}, imm16};//beq 符号扩展
	assign extout = temp << 2; //beq 左移两位 低位补00
	assign j_addr = {pc_4[31:28], imm[25:0], 2'b00};//j的跳转地址拼接
  
	initial begin
		nextpc = 32'h0000_3000;//在仿真开始时，将信号nextpc初始化为十六进制值0x00003000
	end
  
	always@(pcnew, rst)
		if(rst) nextpc = 32'h0000_3000;//若置位 恢复初始
		else if(eret) nextpc=epc;
		else nextpc = pcnew;
  
	always@(*) begin 
		if(IntPc) pcnew = 32'h0000_4180;
		else
			case(npcop) //00:pc+4 01:beq  10:j jal  11:jr
				2'b00: begin 
					pcnew = pcin + 4;
					$display("pc<-pc+4");
				end
				2'b01: begin
					if(zero) begin
						pcnew = pcin + extout;//beq指令跳转地址 pc+4的基础上加上imm符号扩展并左移两位
						$display("beq and zero,pc<-pc+4+(sign_ext(imm16)<<2)");
					end
					else begin
						pcnew = pcin + 4;
						$display("beq and not zero,pc<-pc+4");
					end
				end
				2'b10: begin
					pcnew = j_addr;
					$display("j/jal,pc<-(pc+4)[31:28]||imm26||00");
				end
				2'b11: begin
					pcnew = rd1;
					$display("jr,pc<-R[rs]");
				end
				default: begin
					pcnew = pcin + 4;
					$display("pc<-pc+4");
				end
			endcase
	end
endmodule

