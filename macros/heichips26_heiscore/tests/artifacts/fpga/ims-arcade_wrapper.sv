module ims_arcade_wrapper(
    input CLK_I,          // 10 MHz board oscillator
    input RSTN_ASYNC_I,   // board reset, active low

    // ILI9341 in 8-bit 8080 mode. CSn is tied to GND on the hat, so the bus
    // is ours alone and the engine drives the data lines permanently.
    output logic [7:0] LCD_D,
    output logic LCD_WR_N,
    output logic LCD_DC_N,
    output logic LCD_RD_N,
    output logic LCD_VSYNC,

    // Not driven by the engine: the panel's hardware reset and the backlight.
    output logic LCD_RST_N,
    output logic LCD_BL
);

logic CLK_25MHz;
logic PLL_LOCKED;

pll_10_to_25 pll_inst (
    .clk_10mhz(CLK_I),
    .clk_25mhz(CLK_25MHz),
    .pll_locked(PLL_LOCKED)
);

// The engine never reads, so the bus direction control goes nowhere.
logic lcd_d_en;
logic lcd_rd_n;

my_engine I_DUT (
    .CLK_I(CLK_25MHz),
    .RST_ASYNC_I(~RSTN_ASYNC_I | ~PLL_LOCKED),
    .lcd_d_out(LCD_D),
    .lcd_wr_n(LCD_WR_N),
    .lcd_d_c_n(LCD_DC_N),
    .lcd_vsync(LCD_VSYNC),
    .lcd_rd_n(lcd_rd_n),
    .lcd_d_en(lcd_d_en)
);

always_comb begin
    LCD_RD_N = lcd_rd_n;

    // The engine only issues a software reset (and waits out the panel's own
    // power-on reset), so the hardware reset just follows the board reset.
    LCD_RST_N = RSTN_ASYNC_I;

    // Backlight permanently on.
    LCD_BL = 1'b1;
end

endmodule
