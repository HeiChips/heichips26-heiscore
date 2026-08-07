// SPDX-FileCopyrightText: © 2026 HeiScore Authors
// SPDX-License-Identifier: Apache-2.0

// Olimex GateMate EVB with the IMS Arcade hat: playable Pong, shown on the VGA
// output and the hat's ILI9341 panel at the same time. The engine holds one
// scene and two sinks, so both pictures come from the same game state.


module ims_arcade_pong_top (
    input  wire CLK_I,         // 10 MHz board oscillator
    input  wire RSTN_ASYNC_I,  // board reset, active low

    output logic locked,       // PLL lock indicator

    // VGA out, 1 bit per channel replicated across the resistor ladder.
    output logic VGA_HSYNC,
    output logic VGA_VSYNC,

    output logic VGA_RED3,
    output logic VGA_RED2,
    output logic VGA_RED1,
    output logic VGA_RED0,

    output logic VGA_GREEN3,
    output logic VGA_GREEN2,
    output logic VGA_GREEN1,
    output logic VGA_GREEN0,

    output logic VGA_BLUE3,
    output logic VGA_BLUE2,
    output logic VGA_BLUE1,
    output logic VGA_BLUE0,

    // ILI9341 in 8-bit 8080 mode. CSn is tied to GND on the hat, so the bus
    // is ours alone and the engine drives the data lines permanently.
    output logic [7:0] LCD_D,
    output logic LCD_WR_N,
    output logic LCD_DC_N,
    output logic LCD_RD_N,
    output logic LCD_VSYNC,

    // Not driven by the engine: the panel's hardware reset and the backlight.
    output logic LCD_RST_N,
    output logic LCD_BL,

    // Hat key matrix: two column drives, four row returns, active low.
    output logic [1:0] KEYS_X,
    input  logic [3:0] KEYS_Y
);

logic CLK_25MHz;
logic PLL_LOCKED;

pll_10_to_25 pll_inst (
    .clk_10mhz  (CLK_I),
    .clk_25mhz  (CLK_25MHz),
    .pll_locked (PLL_LOCKED)
);

logic VGA_R, VGA_G, VGA_B;

// The engine never reads, so the bus direction control goes nowhere.
logic lcd_d_en;
logic lcd_rd_n;

heiscore_arcade_engine I_DUT (
    .CLK_I       (CLK_25MHz),
    .RST_ASYNC_I (~RSTN_ASYNC_I | ~PLL_LOCKED),

    .red         (VGA_R),
    .green       (VGA_G),
    .blue        (VGA_B),
    .hsync       (VGA_HSYNC),
    .vsync       (VGA_VSYNC),

    .lcd_d_out   (LCD_D),
    .lcd_wr_n    (LCD_WR_N),
    .lcd_d_c_n   (LCD_DC_N),
    .lcd_vsync   (LCD_VSYNC),
    .lcd_rd_n    (lcd_rd_n),
    .lcd_d_en    (lcd_d_en),

    .KEYS_X      (KEYS_X),
    .KEYS_Y      (KEYS_Y)
);

always_comb begin
    locked = PLL_LOCKED;

    VGA_RED3 = VGA_R;
    VGA_RED2 = VGA_R;
    VGA_RED1 = VGA_R;
    VGA_RED0 = VGA_R;

    VGA_GREEN3 = VGA_G;
    VGA_GREEN2 = VGA_G;
    VGA_GREEN1 = VGA_G;
    VGA_GREEN0 = VGA_G;

    VGA_BLUE3 = VGA_B;
    VGA_BLUE2 = VGA_B;
    VGA_BLUE1 = VGA_B;
    VGA_BLUE0 = VGA_B;

    LCD_RD_N = lcd_rd_n;

    // The engine only issues a software reset (and waits out the panel's own
    // power-on reset), so the hardware reset just follows the board reset.
    LCD_RST_N = RSTN_ASYNC_I;

    LCD_BL = 1'b1;
end

endmodule
