# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1

# RTL of the design under test, shared by all boards. 

SRC_DIR    := ../../../rtl
GEN_DIR    := $(SRC_DIR)/generated
COMMON_DIR := ../../common

DUT_SRCS := \
	$(GEN_DIR)/heiscore_engine.sv \
	$(SRC_DIR)/heichips26_heiscore.sv

DUT_ENGINE_SRCS := $(GEN_DIR)/heiscore_engine.sv
DUT_LCD_SRCS    := $(GEN_DIR)/heiscore_lcd_engine.sv
