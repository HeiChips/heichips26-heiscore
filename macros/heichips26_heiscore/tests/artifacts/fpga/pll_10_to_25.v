module pll_10_to_25 (
    input  wire clk_10mhz,
    output wire clk_25mhz,
    output wire pll_locked
);
`ifdef VERILATOR
    assign clk_25mhz = clk_10mhz;
    assign pll_locked = 1;
`else
    CC_PLL #(
        .REF_CLK(10.0),      // Input clock frequency in MHz
        .OUT_CLK(25.0),      // Desired output clock frequency in MHz
        .PERF_MD("SPEED"),   // Optional: ECONOMY | SPEED | LOWPOWER
        .LOW_JITTER(1),      // Enable low jitter mode
        .LOCK_REQ(1),        // Require stable lock before enabling outputs
        .CLK270_DOUB(0),
        .CLK180_DOUB(0),
        .CI_FILTER_CONST(2),
        .CP_FILTER_CONST(4)
    ) pll_inst (
        .CLK_REF(clk_10mhz),         // 10 MHz input
        .USR_PLL_LOCKED(pll_locked), // Lock indicator
        .CLK0(clk_25mhz),            // Main output (16 MHz, 0°)
        .USR_CLK_REF(),              // Unused
        .CLK_FEEDBACK(),             // Unused
        .USR_LOCKED_STDY_RST(),      // Optional lock reset
        .USR_PLL_LOCKED_STDY(),      // Optional stable lock output
        .CLK90(), .CLK180(), .CLK270(), .CLK_REF_OUT() // Not used
    );
`endif
endmodule
