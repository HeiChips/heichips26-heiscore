# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1

# Board: Olimex GateMate EVB with the IMS Arcade hat, ILI9341 LCD output.
# Drives the LCD engine, not the VGA one. See ../../README.md.

TOP := ims_arcade_top

include ../../dut.mk
MODULES_SYNTH := $(DUT_LCD_SRCS) $(COMMON_DIR)/pll_10_to_25.v ims_arcade_top.sv

PCF_FILE := ims-arcade.ccf

include ../../boards/olimex-gatemate.mk
include ../../fpga.mk
