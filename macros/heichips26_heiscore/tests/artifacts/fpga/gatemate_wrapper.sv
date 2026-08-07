module gatemate_wrapper(
    input CLK_I,
    input RSTN_ASYNC_I,

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

    input  logic [3:0] KEYS_Y,
    output logic [1:0] KEYS_X,

    output logic SPEAKER_PWM

);

logic CLK_25MHz;
logic PLL_LOCKED;

pll_10_to_25 pll_inst (
    .clk_10mhz(CLK_I),
    .clk_25mhz(CLK_25MHz),
    .pll_locked(PLL_LOCKED)
);

logic VGA_R, VGA_B, VGA_G;

my_engine I_DUT (
    .CLK_I(CLK_25MHz),
    .RST_ASYNC_I(~RSTN_ASYNC_I | ~PLL_LOCKED),
    .red(VGA_R),
    .green(VGA_G),
    .blue(VGA_B),
    .hsync(VGA_HSYNC),
    .vsync(VGA_VSYNC),
    .KEYS_X(KEYS_X),
    .KEYS_Y(KEYS_Y),
    .SPEAKER_PWM(SPEAKER_PWM)
);

always_comb begin
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
