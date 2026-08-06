module tt_um_vga_example(
  input  wire [7:0] ui_in,    // Dedicated inputs
  output wire [7:0] uo_out,   // Dedicated outputs
  input  wire [7:0] uio_in,   // IOs: Input path
  output wire [7:0] uio_out,  // IOs: Output path
  output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
  input  wire       ena,      // always 1 when the design is powered, so you can ignore it
  input  wire       clk,      // clock
  input  wire       rst_n     // reset_n - low to reset
);


logic VGA_R, VGA_B, VGA_G;

heiscore_engine I_DUT (
    .CLK_I(clk),
    .RST_ASYNC_I(~rst_n),
    .red(VGA_R),
    .green(VGA_G),
    .blue(VGA_B),
    .hsync(VGA_HSYNC),
    .vsync(VGA_VSYNC)
);

assign uo_out = {VGA_HSYNC, VGA_B, VGA_G, VGA_R, VGA_VSYNC, VGA_B, VGA_G, VGA_R};

// Unused outputs assigned to 0.
assign uio_out = 0;
assign uio_oe  = 0;

endmodule
