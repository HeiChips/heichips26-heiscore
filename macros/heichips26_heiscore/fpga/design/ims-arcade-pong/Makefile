# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1

# Board: Olimex GateMate EVB with the IMS Arcade hat, playable Pong on the VGA
# output and the ILI9341 panel at once. See ../../README.md.

TOP := ims_arcade_pong_top

include ../../dut.mk
MODULES_SYNTH := $(DUT_ARCADE_SRCS) $(COMMON_DIR)/pll_10_to_25.v ims_arcade_pong_top.sv

PCF_FILE := ims-arcade-pong.ccf

include ../../boards/olimex-gatemate.mk
include ../../fpga.mk
