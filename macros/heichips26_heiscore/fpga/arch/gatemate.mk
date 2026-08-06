# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1

# Cologne Chip GateMate: Yosys (synth_gatemate) -> nextpnr-himbaechel -> gmpack.

TARGET     ?= synth_gatemate
SYNTH_OPTS ?= -luttree -nomx8

GATEMATE_DEVICE ?= CCGM1A1

PNR_ARGS    ?= --device $(GATEMATE_DEVICE) --router router2
PNR_OUT     ?= $(BUILD_DIR)/$(TOP)_impl.txt
PNR_CMD     ?= nextpnr-himbaechel $(PNR_ARGS) --json $(BUILD_DIR)/$(TOP).json -o ccf=$(PCF_FILE) -o out=$(PNR_OUT)

BITSTREAM ?= $(BUILD_DIR)/$(TOP).bit
PACK_CMD  ?= gmpack $(PNR_OUT) $(BITSTREAM)
LOAD_CMD  ?= openFPGALoader --board=$(OPENFPGALOADER_BOARD) $(OPENFPGALOADER_FLAGS) $(BITSTREAM)
FLASH_CMD ?= openFPGALoader --board=$(OPENFPGALOADER_BOARD) $(OPENFPGALOADER_FLAGS) --write-flash $(BITSTREAM)
