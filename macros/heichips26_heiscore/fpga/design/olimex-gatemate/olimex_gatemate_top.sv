// SPDX-FileCopyrightText: © 2026 HeiScore Authors
// SPDX-License-Identifier: Apache-2.0

// Olimex GateMate EVB, VGA out. The board oscillator is 10 MHz, so a PLL makes
// the 25 MHz pixel clock. The engine emits 1 bit per channel, replicated across
// each 4-bit VGA channel of the resistor ladder.

module olimex_gatemate_top (
    input  wire  CLK_I,         // 10 MHz board oscillator
    input  wire  RSTN_ASYNC_I,  // board reset, active low

    output logic locked,        // PLL lock indicator

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
    output logic VGA_BLUE0
);

logic CLK_25MHz;
logic PLL_LOCKED;

pll_10_to_25 pll_inst (
    .clk_10mhz  (CLK_I),
    .clk_25mhz  (CLK_25MHz),
    .pll_locked (PLL_LOCKED)
);

logic VGA_R, VGA_G, VGA_B;

heiscore_engine I_DUT (
    .CLK_I       (CLK_25MHz),
    .RST_ASYNC_I (~RSTN_ASYNC_I | ~PLL_LOCKED),
    .red         (VGA_R),
    .green       (VGA_G),
    .blue        (VGA_B),
    .hsync       (VGA_HSYNC),
    .vsync       (VGA_VSYNC)
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
end

endmodule
