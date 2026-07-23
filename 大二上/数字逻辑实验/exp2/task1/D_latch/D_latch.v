module D_latch (D, EN, Q);

   input D;
	input EN;
	
	output Q;
	reg Q;
	
	always @ (D, EN) 
		begin
		if (EN) Q <= D;
		end
