// SPDX-FileCopyrightText: © 2026 HeiScore Authors
// SPDX-License-Identifier: Apache-2.0

// Pin wrapper around the generated engine. Everything below the instance is
// emitted by nortl into heiscore_engine.sv (see src/heiscore/top.py); this file
// only maps it onto the HeiChips interface and is hand-written.
//
// uo_out follows the TinyVGA Pmod order, so the 1-bit colour channels are
// replicated across both halves of the byte.

`default_nettype none

module heichips26_heiscore (
`ifdef USE_POWER_PINS
    inout  wire VPWR,
    inout  wire VGND,
`endif
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    wire _unused = &{ena, ui_in, uio_in};

    logic vga_r, vga_g, vga_b, vga_hsync, vga_vsync;

    heiscore_engine i_engine (
        .CLK_I       (clk),
        .RST_ASYNC_I (~rst_n),
        .red         (vga_r),
        .green       (vga_g),
        .blue        (vga_b),
        .hsync       (vga_hsync),
        .vsync       (vga_vsync)
    );

    assign uo_out  = {vga_hsync, vga_b, vga_g, vga_r, vga_vsync, vga_b, vga_g, vga_r};

    assign uio_out = '0;
    assign uio_oe  = '0;

endmodule
