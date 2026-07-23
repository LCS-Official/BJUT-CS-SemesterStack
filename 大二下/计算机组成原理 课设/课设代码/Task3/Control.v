module Control(
	input wire clk,
	input wire rst,
	input wire [5:0] opcode,
	input wire [5:0] funct,
	input wire zero,
	input wire overflow,
	input wire [4:0] MF,
	input wire IntReq,
	output reg PCWr,
	output reg [1:0] NPCOp,
	output reg [2:0] ALUOp,
	output reg [1:0] EXTOp,
	output reg IRWr,
	output reg GPRWr,
	output reg DMWr,
	output reg [1:0] GPRSel,
	output reg [2:0] WDSel,
	output reg BSel,
	output reg lb,
	output reg sb,
	output reg cp0_wen,
	output reg bridge_wen,
	output reg EXLSet,
	output reg EXLClr,
	output reg IntPc
);

	reg [3:0] cur_state, next_state;
  
	parameter [3:0] S0 = 4'b0000;
	parameter [3:0] S1 = 4'b0001;
	parameter [3:0] S2 = 4'b0010;
	parameter [3:0] S3 = 4'b0011;
	parameter [3:0] S4 = 4'b0100;
	parameter [3:0] S5 = 4'b0101;
	parameter [3:0] S6 = 4'b0110;
	parameter [3:0] S7 = 4'b0111;
	parameter [3:0] S8 = 4'b1000;
	parameter [3:0] S9 = 4'b1001;
	parameter [3:0] S10 = 4'b1010;

	always @ (*)
		begin
			PCWr = 1'b0;
			NPCOp = 2'b00;
			ALUOp = 3'b000;
			EXTOp = 2'b00;
			IRWr = (cur_state == S0);
			GPRWr = 1'b0;
			DMWr = 1'b0;
			WDSel = 3'b000;
			GPRSel = 2'b00;
			BSel = 1'b0;
			lb = 0;
			sb = 0;
			cp0_wen = 0;
			bridge_wen = 0;
			EXLSet = (cur_state == S10);
			EXLClr = 0;
			IntPc = IntReq && (cur_state == S10);
			case (opcode)
				6'b000000:
					case (funct)
						6'b100001: begin	// addu
							ALUOp = 3'b000;
							GPRSel = 2'b01;
							EXTOp = 2'b00;
							BSel = 1'b0;
							WDSel = 3'b000;
							DMWr = 1'b0;
							GPRWr = (cur_state == S7);
							NPCOp = 2'b00;
							PCWr = (cur_state == S0) || (cur_state == S10);
						end
						6'b100011: begin	// subu
							ALUOp = 3'b001;
							GPRSel = 2'b01;
							EXTOp = 2'b00;
							BSel = 1'b0;
							WDSel = 3'b000;
							DMWr = 1'b0;
							GPRWr = (cur_state == S7);
							NPCOp = 2'b00;
							PCWr = (cur_state == S0) || (cur_state == S10);
						end
						6'b101010: begin	// slt
							ALUOp = 3'b011;
							GPRSel = 2'b01;
							EXTOp = 2'b00;
							BSel = 1'b0;
							WDSel = 3'b000;
							DMWr = 1'b0;
							GPRWr = (cur_state == S7);
							NPCOp = 2'b00;
							PCWr = (cur_state == S0) || (cur_state == S10);
						end
						6'b001000: begin	// jr
							ALUOp = 3'b000;
							GPRSel = 2'b00;
							EXTOp = 2'b00;
							BSel = 1'b0;
							WDSel = 3'b000;
							DMWr = 1'b0;
							GPRWr = 1'b0;
							NPCOp = { (cur_state != S0), (cur_state != S0) };
							PCWr = (cur_state == S0) || (cur_state == S9) || (cur_state == S10);
						end
						default:;
				endcase
				6'b001000: begin	// addi
					ALUOp = 3'b100;
					GPRSel = { overflow, overflow };
					EXTOp = 2'b01;
					BSel = 1'b1;
					WDSel = { 1'b0, overflow, overflow };
					DMWr = 1'b0;
					GPRWr = (cur_state == S7);
					NPCOp = 2'b00;
					PCWr = (cur_state == S0) || (cur_state == S10);
				end
				6'b001001: begin	// addiu
					ALUOp = 3'b000;
					GPRSel = 2'b00;
					EXTOp = 2'b01;
					BSel = 1'b1;
					WDSel = 3'b000;
					DMWr = 1'b0;
					GPRWr = (cur_state == S7);
					NPCOp = 2'b00;
					PCWr = (cur_state == S0) || (cur_state == S10);
				end
				6'b001101: begin	// ori
					ALUOp = 3'b010;
					GPRSel = 2'b00;
					EXTOp = 2'b00;
					BSel = 1'b1;
					WDSel = 3'b000;
					DMWr = 1'b0;
					GPRWr = (cur_state == S7);
					NPCOp = 2'b00;
					PCWr = (cur_state == S0) || (cur_state == S10);
				end
				6'b001111: begin	// lui
					ALUOp = 3'b000;
					GPRSel = 2'b00;
					EXTOp = 2'b10;
					BSel = 1'b1;
					WDSel = 3'b000;
					DMWr = 1'b0;
					GPRWr = (cur_state == S7);
					NPCOp = 2'b00;
					PCWr = (cur_state == S0) || (cur_state == S10);
				end
				6'b100011: begin	// lw
					ALUOp = 3'b000;
					GPRSel = 2'b00;
					EXTOp = 2'b01;
					BSel = 1'b1;
					WDSel = 3'b001;
					DMWr = 1'b0;
					GPRWr = (cur_state == S4);
					NPCOp = 2'b00;
					PCWr = (cur_state == S0) || (cur_state == S10);
				end
				6'b100000: begin	// lb
					ALUOp = 3'b000;
					GPRSel = 2'b00;
					EXTOp = 2'b01;
					BSel = 1'b1;
					WDSel = 3'b001;
					DMWr = 1'b0;
					GPRWr = (cur_state == S4);
					NPCOp = 2'b00;
					PCWr = (cur_state == S0) || (cur_state == S10);
					lb = 1;
				end
				6'b101011: begin	// sw
					ALUOp = 3'b000;
					GPRSel = 2'b00;
					EXTOp = 2'b01;
					BSel = 1'b1;
					WDSel = 3'b000;
					DMWr = (cur_state == S5);
					GPRWr = 1'b0;
					NPCOp = 2'b00;
					PCWr = (cur_state == S0) || (cur_state == S10);
					bridge_wen = (cur_state == S5);
				end
				6'b101000: begin	// sb
					ALUOp = 3'b000;
					GPRSel = 2'b00;
					EXTOp = 2'b01;
					BSel = 1'b1;
					WDSel = 3'b000;
					DMWr = (cur_state == S5);
					GPRWr = 1'b0;
					NPCOp = 2'b00;
					PCWr = (cur_state == S0) || (cur_state == S10);
					sb = 1;
					bridge_wen = (cur_state == S5);
				end
				6'b000100: begin	// beq
					ALUOp = 3'b001;
					GPRSel = 2'b00;
					EXTOp = 2'b00;
					BSel = 1'b0;
					WDSel = 3'b000;
					DMWr = 1'b0;
					GPRWr = 1'b0;
					NPCOp = {1'b0, (cur_state != S0)};
					PCWr = (cur_state == S0) || (zero && (cur_state == S8)) || (cur_state == S10);
				end
				6'b000010: begin	// j
					ALUOp = 3'b000;
					GPRSel = 2'b00;
					EXTOp = 2'b00;
					BSel = 1'b0;
					WDSel = 3'b000;
					DMWr = 1'b0;
					GPRWr = 1'b0;
					NPCOp = {(cur_state != S0), 1'b0};
					PCWr = (cur_state == S0) || (cur_state == S9) || (cur_state == S10);
				end
				6'b000011: begin	// jal
					ALUOp = 3'b000;
					GPRSel = 2'b10;
					EXTOp = 2'b00;
					BSel = 1'b0;
					WDSel = 3'b010;
					DMWr = 1'b0;
					GPRWr = (cur_state == S9);
					NPCOp = {(cur_state != S0), 1'b0};
					PCWr = (cur_state == S0) || (cur_state == S9) || (cur_state == S10);
				end
				6'b010000: begin
					PCWr = (cur_state == S0) || (cur_state == S9)  || (cur_state == S10);
					if(funct == 6'b011000)	// ERET
						begin
							EXLClr = 1;
							PCWr = (cur_state == S9);
						end
					else if(MF == 5'b00000)	// MFC0
						begin
							WDSel = 3'b100;
							GPRWr = (cur_state == S4);
						end
					else if(MF == 5'b00100)	// MTC0
						cp0_wen = (cur_state == S5);
				end
				default:;
			endcase
		end
		
	always @ (posedge clk, posedge rst)
		if(rst)
			cur_state <= S0;
		else
			cur_state <= next_state;

	always @ (*)
		case (cur_state)
			S0: next_state = S1;
			S1: begin
				if (opcode == 6'b100011 || opcode == 6'b100000 || opcode == 6'b101011 || opcode == 6'b101000)
					next_state = S2;
				else if ((opcode == 6'b000000 && (funct == 6'b100001 || funct == 6'b100011 || funct == 6'b101010)) ||
							opcode == 6'b001101 || opcode == 6'b001000 || opcode == 6'b001001 || opcode == 6'b001111)
					next_state = S6;
				else if (opcode==6'b000100)
					next_state = S8;
				else if (opcode == 6'b000010 || opcode == 6'b000011 || (opcode == 6'b000000 && funct == 6'b001000))
					next_state = S9;
				else if (opcode == 6'b010000)
					begin
						if (funct == 6'b011000)
							next_state = S9;
						else if (MF   == 5'b00000)
							next_state = S4;
						else if (MF   == 5'b00100)
							next_state = S5;
						else
							next_state = S0;
					end
				else
					next_state = S0;
			end
			S2: begin
				if (opcode == 6'b100011 || opcode == 6'b100000)
					next_state = S3;
				else if (opcode == 6'b101011 || opcode == 6'b101000)
					next_state = S5;
				else
					next_state = S0;
			end
			S3: next_state = S4;
			S4: if(!IntReq) next_state = S0;	else next_state = S10;
			S5: if(!IntReq) next_state = S0;	else next_state = S10;
			S6: next_state = S7;
			S7: if(!IntReq) next_state = S0;	else next_state = S10;
			S8: if(!IntReq) next_state = S0;	else next_state = S10;
			S9: if(!IntReq) next_state = S0;	else next_state = S10;
			S10: next_state = S0;
			default: next_state = S0;
		endcase

endmodule