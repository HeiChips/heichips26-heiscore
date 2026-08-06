# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1

# Board: Olimex GateMate EVB (CCGM1A1), VGA output. See ../../README.md.

TOP := olimex_gatemate_top

include ../../dut.mk
MODULES_SYNTH := $(DUT_ENGINE_SRCS) $(COMMON_DIR)/pll_10_to_25.v olimex_gatemate_top.sv

PCF_FILE := olimex-gatemate.ccf

include ../../boards/olimex-gatemate.mk
include ../../fpga.mk
