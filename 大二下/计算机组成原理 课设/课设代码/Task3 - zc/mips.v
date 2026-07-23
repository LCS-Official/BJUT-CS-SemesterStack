module mips(clk, rst, in) ; 
  input clk ; 
  input rst ;
  input [31:0] in;
  
  wire [31:0] pcout,nextpc,busa,instruct,pc_4,gpr_datain,
                aluout,dout,busb,extout,alu_b;
  wire [1:0] npcop,gprsel,extop;
  wire zero,bsel,gprwr,dmwr,overflow,we; 
  wire [4:0] gpr_rd;
  wire [2:0] aluop;

wire [31:0] aluoutout,arout,brout,drout,irout,epc,prrd,dev0_rd,dev2_rd
            ,dev_wd,dmin,cp0dout,switchout;
wire irwr,pcwr,lb_flag,sb_flag,EXLClr,bridge_wen,dev0_we, dev2_we,irq,
        cp0_wen,EXLSet,IntReq;

wire[5:0] hwint;

wire [2:0] wdsel;

wire[3:0] dev_addr;

bridge b1(aluoutout, brout, prrd, dev0_rd, switchout, dev2_rd, 
            dev_wd, dev_addr, bridge_wen, dev0_we, dev2_we, hwint, irq,change,chan);

cp0 cp01(pcout, brout, hwint, irout[15:11], cp0_wen, EXLSet, EXLClr, 
            clk, rst, IntReq, epc, cp0dout);

output_dev outdev(clk, dev2_we, dev_addr, dev_wd, dev2_rd);  ////dev2_rd 从output_dev读出数据，送到bridge

timer timer(clk, rst, dev_addr, dev0_we, dev_wd, dev0_rd, irq,change); //dev0_rd 从timer读出数据，送到bridge

sel_wd_dmin s4(aluoutout,prrd, drout, dmin);
  
pc p1(clk, nextpc, pcout,pcwr);
  
npc n1(pcout, busa, npcop, zero, irout[25:0], nextpc, pc_4, rst, IntPc, epc, EXLClr);

im_1k i1(pcout[9:0], instruct) ;
  
sel_gpr_rd s1(gprsel, irout[20:16], irout[15:11], gpr_rd);
  
sel_gpr_datain s2(wdsel, aluout, dmin, pc_4, gpr_datain,cp0dout);
  
sel_alu_b s3(bsel, brout, extout, alu_b);
  
gpr g1(clk, rst, gprwr,gpr_rd, gpr_datain, irout[25:21], irout[20:16], busa, busb,overflow);
  
dm_1k d1( aluoutout[9:0], busb, we, clk, dout,lb_flag,sb_flag);
  
ext e1(irout[15:0], extop, extout);
  
alu a1(arout, alu_b, aluop, zero, overflow, aluout);

controller c1(irout[31:26], irout[5:0], aluop, gprsel, gprwr, extop, we,
                   wdsel, npcop, bsel, overflow,
                   clk,rst,pcwr,irwr,lb_flag,sb_flag,zero,
                   IntReq,EXLSet,EXLClr,cp0_wen,bridge_wen,IntPc,irout[25:21],chan);

aluout aluout1(clk, aluout, aluoutout);
ar ar1(clk, busa, arout);
br br1 (clk, busb, brout);
dr dr1(clk, dout, drout);
ir ir1(irwr,clk,instruct,irout);

switch switch(in,switchout);

endmodule