# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1

MAKEFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

RUN_TAG = $(shell ls -1 $(LIBRELANE_DIR)/runs 2>/dev/null | tail -n 1)

# Variables
TOP = heichips26_heiscore

.DEFAULT_GOAL := help

# Cell name for verification targets (default: top-level cell)
# Override with: make <target> CELL=<cellname>
CELL ?= $(TOP)

# Set the waveform viewer GTKWave or Surfer (default: gtkwave)
# Override with: make <target> WAVEFORM_VIEWER=<gtkwave|surfer>
WAVEFORM_VIEWER ?= gtkwave

# Folder structure
MACROS_DIR      := macros
COCOTB_DIR      := testbenches/cocotb
VERILOG_TB_DIR 	:= testbenches/verilog
VERILATOR_TB_DIR := testbenches/verilator
TEST_DIR       	:= tests
TEST_ART_DIR   	:= $(TEST_DIR)/artifacts
REPORT_DIR     	:= verification
SRC_DIR 		:= rtl
GEN_DIR 		:= $(SRC_DIR)/generated
NET_NL_DIR    	:= netlist/nl
NET_PNL_DIR  	:= netlist/pnl
NET_SPICE_DIR 	:= netlist/spice
LIBRELANE_DIR 	:= flow/librelane
FLOW_FINAL_DIR 	:= flow/final
FINAL_DIR      	:= final

# Python side: the nortl generator that emits $(GEN_DIR)/*.sv. That directory is
# git-ignored from the inside, so the engines are build products like any other
# and every target below regenerates them on demand.
PY_DIR       := src
PY_SRCS      := $(shell find $(PY_DIR) -name '*.py' 2>/dev/null)
ENGINE       := $(GEN_DIR)/heiscore_engine.sv
LCD_ENGINE   := $(GEN_DIR)/heiscore_lcd_engine.sv
PYTHON       := PYTHONPATH=$(MAKEFILE_DIR)/$(PY_DIR):$$PYTHONPATH python3

# Variables for simulation and linting targets. The engine is generated; the
# LCD engine is FPGA-only and carries its own copy of the nortl_* modules, so it
# is never read alongside $(ENGINE).
MODULES_SYNTH := \
	$(ENGINE) \
	$(SRC_DIR)/heichips26_heiscore.sv

MODULES_SIM := \
	$(MODULES_SYNTH)

# Lint waivers for the generated engines (see rtl/generated.vlt). Kept out of
# MODULES_SYNTH so yosys and LibreLane never see it.
LINT_WAIVERS := $(SRC_DIR)/generated.vlt

# nortl flattens every state guard into one expression, so a single line of the
# generated engine runs past Verilator's default cap of 40k preprocessor tokens
# per line and the parser then dies on the truncated line.
VERILATOR_PREPROC := --preproc-token-limit 400000

# Source file for a single non-TOP CELL: hand-written $(SRC_DIR) first, then the
# generated engines in $(GEN_DIR) (prefers .sv, falls back to .v)
_CELL_SRC = $(or $(wildcard $(SRC_DIR)/$(CELL).sv),$(wildcard $(GEN_DIR)/$(CELL).sv),$(SRC_DIR)/$(CELL).v)

# Source files for sim-rtl-verilog: auto-selects MODULES_SIM when CELL == TOP, single-file otherwise
_SIM_SRCS = $(if $(filter $(CELL),$(TOP)),$(MODULES_SIM),$(_CELL_SRC))

# Source files for lint-verilog: all synthesis sources for TOP, single-file otherwise
_LINT_SRCS = $(if $(filter $(CELL),$(TOP)),$(MODULES_SYNTH),$(_CELL_SRC))

# Testbench extension: prefers <CELL>_tb.sv, falls back to <CELL>_tb.v (dot is added at use site)
_TB_EXT = $(if $(wildcard $(VERILOG_TB_DIR)/$(CELL)_tb.sv),sv,v)


# Help Target
help: ## Show this help message
	@echo 'Usage: make <target> [CELL=<cellname>] [WAVEFORM_VIEWER=<gtkwave|surfer>]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z0-9_.-]+:.*## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ''
	@echo 'CELL defaults to $(TOP). Override to lint or simulate subcells.'
	@echo 'WAVEFORM_VIEWER defaults to gtkwave. Use surfer to launch Surfer instead.'
.PHONY: help
# ================================================================================================

rtl: $(ENGINE) $(LCD_ENGINE) ## Regenerate the engine RTL from the nortl sources
.PHONY: rtl

$(ENGINE): $(PY_SRCS)
	$(PYTHON) -m heiscore.top

$(LCD_ENGINE): $(PY_SRCS)
	$(PYTHON) -m heiscore.top lcd

pytest: ## Run the Python test suite (unit tests, LVS-VGA check, FPGA flows)
	cd $(MAKEFILE_DIR) && $(PYTHON) -m pytest tests
.PHONY: pytest
# ================================================================================================


# Linter Targets
# The "| rtl" order-only prerequisite here and below emits the engines if they are
# missing or older than the nortl sources; it is a no-op once they are up to date.
lint-verilog: | rtl ## Lint Verilog source files with Verilator (usage: make lint-verilog [CELL=<cellname>])
	verilator --lint-only $(VERILATOR_PREPROC) --top-module $(CELL) -I"$(SRC_DIR)" -I"$(GEN_DIR)" $(LINT_WAIVERS) $(_LINT_SRCS)
.PHONY: lint-verilog

lint-verilog-all: ## Lint all Verilog source files (pin wrapper + generated engine)
	$(MAKE) lint-verilog
.PHONY: lint-verilog-all
# ================================================================================================


# Simulation Targets
sim-rtl-verilog: | rtl ## Run RTL simulation of CELL cell with Icarus Verilog (usage: make sim-rtl-verilog [CELL=<cellname>])
	iverilog -g2012 -DSIM -o $(VERILOG_TB_DIR)/test_$(CELL) $(_SIM_SRCS) $(VERILOG_TB_DIR)/$(CELL)_tb.$(_TB_EXT)
	cd $(VERILOG_TB_DIR) && vvp test_$(CELL) -fst
	rm -f $(VERILOG_TB_DIR)/test_$(CELL)
.PHONY: sim-rtl-verilog

sim-view-verilog: ## View CELL cell Verilog simulation waveforms (usage: make sim-view-verilog [CELL=<cellname>] [WAVEFORM_VIEWER=<gtkwave|surfer>])
	@if [ "$(WAVEFORM_VIEWER)" = "gtkwave" ]; then \
		$(WAVEFORM_VIEWER) $(VERILOG_TB_DIR)/$(CELL)_tb.fst $(VERILOG_TB_DIR)/$(CELL)_tb.gtkw; \
	elif [ "$(WAVEFORM_VIEWER)" = "surfer" ]; then \
		$(WAVEFORM_VIEWER) -s $(VERILOG_TB_DIR)/$(CELL)_tb.surf.ron $(VERILOG_TB_DIR)/$(CELL)_tb.fst; \
	else \
		$(WAVEFORM_VIEWER) $(VERILOG_TB_DIR)/$(CELL)_tb.fst; \
	fi
.PHONY: sim-view-verilog

sim-rtl-cocotb: | rtl ## Run RTL simulation of CELL cell with cocotb (usage: make sim-rtl-cocotb [CELL=<cellname>])
	cd $(COCOTB_DIR) && python3 $(CELL)_tb.py
.PHONY: sim-rtl-cocotb

sim-gl-cocotb: ## Run gate-level simulation of CELL cell with cocotb (usage: make sim-gl-cocotb [CELL=<cellname>])
	cd $(COCOTB_DIR) && GL=1 python3 $(CELL)_tb.py
.PHONY: sim-gl-cocotb

sim-view-cocotb: ## View CELL cell cocotb simulation waveforms (usage: make sim-view-cocotb [CELL=<cellname>] [WAVEFORM_VIEWER=<gtkwave|surfer>])
	@if [ "$(WAVEFORM_VIEWER)" = "gtkwave" ]; then \
		$(WAVEFORM_VIEWER) $(COCOTB_DIR)/sim_build/$(CELL).fst $(COCOTB_DIR)/$(CELL)_tb.gtkw; \
	elif [ "$(WAVEFORM_VIEWER)" = "surfer" ]; then \
		$(WAVEFORM_VIEWER) -s $(COCOTB_DIR)/$(CELL)_tb.surf.ron $(COCOTB_DIR)/sim_build/$(CELL).fst; \
	else \
		$(WAVEFORM_VIEWER) $(COCOTB_DIR)/sim_build/$(CELL).fst; \
	fi
.PHONY: sim-view-cocotb

sim-all: ## Simulate the macro (RTL Verilog + RTL/GL cocotb for heichips26_heiscore)
	$(MAKE) sim-rtl-verilog
	$(MAKE) sim-rtl-cocotb
	$(MAKE) sim-gl-cocotb
.PHONY: sim-all
# ================================================================================================


# LibreLane Targets
# config.yaml reads $(ENGINE), so every hardening entry point regenerates first.
librelane: | rtl ## Run LibreLane with Magic and KLayout DRC checks.
	librelane $(LIBRELANE_DIR)/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --save-views-to $(FLOW_FINAL_DIR)/
.PHONY: librelane

librelane-nodrc: | rtl ## Run LibreLane without DRC checks
	librelane $(LIBRELANE_DIR)/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --save-views-to $(FLOW_FINAL_DIR)/ --skip KLayout.DRC --skip Magic.DRC
.PHONY: librelane-nodrc

librelane-magicdrc: | rtl ## Run LibreLane with only Magic DRC checks
	librelane $(LIBRELANE_DIR)/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --save-views-to $(FLOW_FINAL_DIR)/ --skip KLayout.DRC
.PHONY: librelane-magicdrc

librelane-klayoutdrc: | rtl ## Run LibreLane with only KLayout DRC checks
	librelane $(LIBRELANE_DIR)/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --save-views-to $(FLOW_FINAL_DIR)/ --skip Magic.DRC
.PHONY: librelane-klayoutdrc

librelane-openroad: ## Open the last LibreLane run in OpenROAD GUI
	librelane $(LIBRELANE_DIR)/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --last-run --flow OpenInOpenROAD
.PHONY: librelane-openroad

librelane-klayout: ## Open the last LibreLane run in KLayout
	librelane $(LIBRELANE_DIR)/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --last-run --flow OpenInKLayout
.PHONY: librelane-klayout
# ================================================================================================


# Copy Targets
# Using * wildcard to ignore step numbers
copy-reports: ## Copy yosys, antenna, STA, power, IR-drop, DRC, LVS and manufacturability reports from the last LibreLane run to verification/
	rm -rf $(REPORT_DIR)/
	mkdir -p $(REPORT_DIR)/
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-yosys-synthesis/reports/pre_synth_chk.rpt $(REPORT_DIR)/yosys_synth_check.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-yosys-synthesis/reports/pre_techmap.rpt $(REPORT_DIR)/yosys_pre_techmap.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-yosys-synthesis/reports/post_dff.rpt $(REPORT_DIR)/yosys_post_dff.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-yosys-synthesis/reports/stat.rpt $(REPORT_DIR)/stat.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-openroad-checkantennas-1/reports/antenna.rpt $(REPORT_DIR)/antenna_violations.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-openroad-checkantennas-1/reports/antenna_summary.rpt $(REPORT_DIR)/antenna_summary.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-openroad-stapostpnr/summary.rpt $(REPORT_DIR)/stapostpnr_summary.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-openroad-stapostpnr/nom_fast_1p32V_m40C/power.rpt $(REPORT_DIR)/stapostpnr_nom_fast_1p32V_m40C_power.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-openroad-stapostpnr/nom_slow_1p08V_125C/power.rpt $(REPORT_DIR)/stapostpnr_nom_slow_1p08V_125C_power.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-openroad-stapostpnr/nom_typ_1p20V_25C/power.rpt $(REPORT_DIR)/stapostpnr_nom_typ_1p20V_25C_power.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-openroad-irdropreport/irdrop.rpt $(REPORT_DIR)/irdrop.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-magic-drc/reports/drc.magic.rpt $(REPORT_DIR)/drc.magic.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-klayout-drc/reports/drc.klayout.json $(REPORT_DIR)/drc.klayout.json
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-netgen-lvs/reports/lvs.netgen.rpt $(REPORT_DIR)/lvs.netgen.rpt
	cp $(LIBRELANE_DIR)/runs/${RUN_TAG}/*-misc-reportmanufacturability/manufacturability.rpt $(REPORT_DIR)/manufacturability.rpt
.PHONY: copy-reports

copy-final: ## Copy final output gds, lef, lib, nl, pnl, spef, vh and render folders from the last LibreLane run to final/
	rm -rf $(FINAL_DIR)/
	mkdir -p $(FINAL_DIR)/
	cp -r $(FLOW_FINAL_DIR)/gds    $(FINAL_DIR)/gds
	cp -r $(FLOW_FINAL_DIR)/lef    $(FINAL_DIR)/lef
	cp -r $(FLOW_FINAL_DIR)/lib    $(FINAL_DIR)/lib
	cp -r $(FLOW_FINAL_DIR)/nl     $(FINAL_DIR)/nl
	cp -r $(FLOW_FINAL_DIR)/pnl    $(FINAL_DIR)/pnl
	cp -r $(FLOW_FINAL_DIR)/spef   $(FINAL_DIR)/spef
	cp -r $(FLOW_FINAL_DIR)/vh     $(FINAL_DIR)/vh
	cp -r $(FLOW_FINAL_DIR)/render $(FINAL_DIR)/render
.PHONY: copy-final

copy-netlist: ## Copy final output spice, pnl and nl netlists from the last LibreLane run to netlist/
	rm -rf $(NET_SPICE_DIR)/
	mkdir -p $(NET_SPICE_DIR)/
	cp -r $(FLOW_FINAL_DIR)/spice/${TOP}.spice $(NET_SPICE_DIR)/${TOP}.spice

	rm -rf $(NET_PNL_DIR)/
	mkdir -p $(NET_PNL_DIR)/
	cp -r $(FLOW_FINAL_DIR)/pnl/${TOP}.pnl.v $(NET_PNL_DIR)/${TOP}.pnl.v

	rm -rf $(NET_NL_DIR)/
	mkdir -p $(NET_NL_DIR)/
	cp -r $(FLOW_FINAL_DIR)/nl/${TOP}.nl.v $(NET_NL_DIR)/${TOP}.nl.v
.PHONY: copy-netlist
# ================================================================================================


# Build Targets
build-fpga: | rtl ## Build FPGA bitstream (usage: make build-fpga [BOARD=olimex-gatemate])
	@$(MAKE) -C fpga all
.PHONY: build-fpga

load-fpga: ## Load FPGA bitstream into SRAM (usage: make load-fpga [BOARD=olimex-gatemate])
	@$(MAKE) -C fpga load_bitstream
.PHONY: load-fpga

flash-fpga: ## Write FPGA bitstream to flash (usage: make flash-fpga [BOARD=olimex-gatemate])
	@$(MAKE) -C fpga flash_bitstream
.PHONY: flash-fpga

build-top: ## Build macro (run LibreLane with KLayout & Magic DRC checks, copy reports, copy final files, and copy netlists)
	$(MAKE) librelane
	$(MAKE) copy-reports
	$(MAKE) copy-final
	$(MAKE) copy-netlist
#	$(MAKE) librelane-openroad
.PHONY: build-top
# ================================================================================================


# DRC & LVS Verification Targets
# The LibreLane flow already includes DRC and LVS checks with Magic and KLayout, and they are saved in the verification/ folder.
# ================================================================================================


# Lint, Build, Verify and Simulate All Target
all: ## Regenerate RTL, lint, build, verify and simulate the TOP cell
	$(MAKE) rtl
	$(MAKE) lint-verilog-all
	$(MAKE) build-fpga
	$(MAKE) build-top
	$(MAKE) sim-all
.PHONY: all
# ================================================================================================


# Clean Targets
clean: ## Delete all generated files and folders of the TOP cell (LibreLane outputs, final, netlist, reports, simulation and FPGA outputs)
	rm -rf $(LIBRELANE_DIR)/runs $(FLOW_FINAL_DIR)
	rm -rf final netlist
	rm -rf $(REPORT_DIR)
	rm -rf $(COCOTB_DIR)/sim_build $(VERILOG_TB_DIR)/*.fst
	rm -rf $(VERILATOR_TB_DIR)/obj_* $(VERILATOR_TB_DIR)/*.ppm $(VERILATOR_TB_DIR)/*_nl.v $(VERILATOR_TB_DIR)/sg13cmos5l_verilator.v
	$(MAKE) clean-tests
	find $(GEN_DIR) -mindepth 1 ! -name .gitignore -delete
	@$(MAKE) -C fpga clean
.PHONY: clean

clean-tests: ## Delete the files the pytest suite generates under tests/artifacts (checked-in inputs stay)
	rm -f  $(TEST_ART_DIR)/fpga/*_yosys.* $(TEST_ART_DIR)/fpga/*.bit \
	       $(TEST_ART_DIR)/fpga/*impl.txt $(TEST_ART_DIR)/fpga/*rendered.sv
	rm -f  $(TEST_ART_DIR)/vga_playground/*rendered.sv $(TEST_ART_DIR)/vga_playground/*rendered.v
	rm -rf $(TEST_DIR)/.pytest_cache
	find $(TEST_DIR) -name __pycache__ -type d -prune -exec rm -rf {} +
.PHONY: clean-tests

clean-macros: ## Delete all generated files and folders of all macros
#	ToDo: this design currently has no macros under $(MACROS_DIR)/
.PHONY: clean-macros

clean-all: ## Delete all generated files and folders of the macros and the TOP cell
	$(MAKE) clean-macros
	$(MAKE) clean
.PHONY: clean-all
# ================================================================================================
