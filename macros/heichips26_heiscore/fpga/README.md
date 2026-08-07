# FPGA Emulation Flow

This directory holds the FPGA emulation flow for this project's **top-level
design** (`heichips26_heiscore`, defined in
`../rtl/heichips26_heiscore.sv`), across several boards. Each board wraps it
in a `<board>_top.sv` that maps board pins to the TinyTapeout-style
`ui_in`/`uo_out`/`uio_*`/`ena`/`clk`/`rst_n` interface.

> [!NOTE]
> To emulate a single macro on its own (e.g. `counter`, without the
> top-level wrapper), see `../macros/counter/fpga/`. Both flows share the
> same recipe logic from `fpga.mk` — see below.

| Board                                               | Directory                      | Toolchain                                        | Status                                   |
| --------------------------------------------------- | ------------------------------ | ------------------------------------------------ | ---------------------------------------- |
| Olimex GateMate EVB                                 | `fpga/design/olimex-gatemate/` | Yosys → nextpnr-himbaechel → gmpack              | Build verified, **default**              |
| Olimex GateMate EVB + IMS Arcade hat                | `fpga/design/ims-arcade/`      | Yosys → nextpnr-himbaechel → gmpack              | Build verified                           |
| Olimex GateMate EVB + IMS Arcade hat, playable Pong | `fpga/design/ims-arcade-pong/` | Yosys → nextpnr-himbaechel → gmpack              | Build verified                           |
| iCEBreaker                                          | `fpga/design/icebreaker/`      | Yosys → nextpnr-ice40 → icepack                  | Build verified, flash untested           |
| ULX3S                                               | `fpga/design/ulx3s/`           | Yosys → nextpnr-ecp5 → ecppack                   | Tested, hardware flash-verified, default |
| Tang Nano 9K                                        | `fpga/design/nano9k/`          | Yosys → nextpnr-himbaechel → gowin_pack          | Build verified, flash untested           |
| Basys 3                                             | `fpga/design/basys3/`          | Yosys → nextpnr-xilinx → prjxray (`nix-openxc7`) | Tested, hardware flash-verified          |
| Boolean                                             | `fpga/design/boolean/`         | Yosys → nextpnr-xilinx → prjxray (`nix-openxc7`) | Build verified, flash untested           |
| pico-ice                                            | `fpga/design/pico-ice/`        | Yosys → nextpnr-ice40 → icepack                  | Build verified, flash untested           |

All boards need `yosys`; the iCE40/ECP5/Gowin boards additionally need
`nextpnr-ice40`/`nextpnr-ecp5`/`nextpnr-himbaechel`, `icepack`/`ecppack`/
`gowin_pack`, and `openFPGALoader` — all provided by this repo's main Nix flake
(`nix develop`). Basys 3 and Boolean instead need `nextpnr-xilinx` + `prjxray`,
which come from a **separate** nix shell vendored at the repo root
(`nix-openxc7/`), not the main flake. From `fpga/`, enter it with:

```sh
nix develop ../../../nix-openxc7
```

Once inside, they build like any other board (`make -C design/basys3 all`, etc.).

## Shared flow: `fpga.mk`

`fpga.mk` implements the whole flow (synthesis, place-and-route,
bitstream, flash) as targets parametrized by variables, split across four
layers:

- `fpga.mk` — the targets themselves, plus defaults common to all boards
- `arch/<arch>.mk` — one per FPGA architecture (`ice40`, `ecp5`, `gowin`,
  `xilinx7`): the synthesis, place-and-route and packing toolchain
- `boards/<board>.mk` — one per board: device, package, and how to flash
- `dut.mk` — one per DUT tree (this directory vs. `macros/counter/fpga/`):
  the RTL under test, shared by every board's `Makefile` in that tree

A board directory's `Makefile` is thin. It includes `dut.mk` for the DUT
sources, names the board top wrapper and the pin file, then includes its
`boards/` fragment and `fpga.mk`, which in turn pulls in the `arch/`
fragment named by the board's `ARCH`:

```make
TOP := counter

include ../dut.mk
MODULES_SYNTH := $(DUT_SRCS)

PCF_FILE := icebreaker.pcf

include ../../../../fpga/boards/icebreaker.mk
include ../../../../fpga/fpga.mk
```

### Set by `dut.mk`

| Variable   |           | Description                                                                       |
| ---------- | --------- | --------------------------------------------------------------------------------- |
| `SRC_DIR`  | mandatory | RTL source directory                                                              |
| `DUT_SRCS` | mandatory | Ordered source file list for the design under test, without the board top wrapper |

### Set by the board `Makefile`

| Variable        |           | Description                                                                                          |
| --------------- | --------- | ---------------------------------------------------------------------------------------------------- |
| `TOP`           | mandatory | Synthesis top module / instance name                                                                 |
| `MODULES_SYNTH` | mandatory | Ordered source file list for `TOP` — usually `$(DUT_SRCS)` plus the board's `<board>_top.sv` wrapper |
| `PCF_FILE`      | mandatory | Board pin constraint file                                                                            |

### Set by `boards/<board>.mk`

| Variable                                                             |           | Description                                                                                          |
| -------------------------------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------- |
| `ARCH`                                                               | mandatory | Selects the `arch/<arch>.mk` fragment                                                                |
| `ICE40_DEVICE`, `ECP5_DEVICE`, `GOWIN_DEVICE`/`GOWIN_FAMILY`, `PART` | mandatory | Device and package, whichever the board's arch uses                                                  |
| `CHIPDB`, `XRAY_FAMILY`                                              | mandatory | `xilinx7` only                                                                                       |
| `OPENFPGALOADER_BOARD`                                               | mandatory | openFPGALoader board profile, unless `LOAD_CMD`/`FLASH_CMD` are set instead                          |
| `OPENFPGALOADER_FLAGS`                                               | optional  | Extra openFPGALoader flags                                                                           |
| `LOAD_CMD`                                                           | optional  | Complete SRAM load command, replacing the openFPGALoader default, for boards it has no profile for   |
| `FLASH_CMD`                                                          | optional  | Complete flash write command, replacing the openFPGALoader default, for boards it has no profile for |

### Set by `arch/<arch>.mk`

| Variable                |           | Description                                                                                                                                                          |
| ----------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TARGET`, `SYNTH_OPTS`  | mandatory | Yosys synth pass and its options                                                                                                                                     |
| `SYNTH_CMD`             | optional  | Complete synthesis command, replacing `TARGET`/`SYNTH_OPTS`, for a synth pass that doesn't fit the `$(TARGET) $(SYNTH_OPTS) -top $(TOP)` shape (e.g. `synth_xilinx`) |
| `PNR_CMD`, `PNR_OUT`    | mandatory | Place-and-route command and its output file                                                                                                                          |
| `PNR_ARGS`, `PNR_DEPS`  | optional  | PnR flags, and extra prerequisites (e.g. a generated chipdb)                                                                                                         |
| `PACK_CMD`, `BITSTREAM` | mandatory | Bitstream packing command and output file                                                                                                                            |

Both fragments assign with `?=` throughout, so a board `Makefile` can still
override anything.

### Adding a board

- Create `boards/<board>.mk`, setting `ARCH` and the device, package, and
  flash variables above.
- Create the board directory under `design/`: its `Makefile`
  (`include ../../dut.mk`, `TOP`, `MODULES_SYNTH`, and `PCF_FILE`, then the
  two remaining `include`s), the pin constraint file it names, and a
  `<board>_top.sv` wrapper mapping board pins to the TinyTapeout-style
  interface.
- If the board's FPGA family is new, also create `arch/<arch>.mk` with that
  family's synthesis, place-and-route, and packing toolchain.

`fpga.mk` itself does not change.

## Picking a board

`fpga/Makefile` is a thin dispatcher — it forwards every target to
`fpga/design/$(BOARD)/Makefile`, defaulting to `BOARD := olimex-gatemate`:

```make
BOARD ?= olimex-gatemate
%:
	$(MAKE) -C design/$(BOARD) $@
```

So from `fpga/` you can either run the default board directly...

```sh
make all              # olimex-gatemate
```

...or pick another board with `BOARD=`, or `cd` into its directory —
both are equivalent:

```sh
make BOARD=icebreaker all
make -C design/icebreaker all
```

The engines under `../rtl/generated/` are emitted by `make rtl` in the macro root
and are not part of the checkout — run it once, and again whenever the nortl
sources change. `make build-fpga` from the macro root does that for you; entering
this tree directly does not. `dut.mk` offers three source sets, because the boards
do not all wrap the same thing:

| Variable          | Sources                                      | Used by                                 |
| ----------------- | -------------------------------------------- | --------------------------------------- |
| `DUT_SRCS`        | pin wrapper + `generated/heiscore_engine.sv` | boards emulating the submitted top cell |
| `DUT_ENGINE_SRCS` | `generated/heiscore_engine.sv`               | `olimex-gatemate`                       |
| `DUT_LCD_SRCS`    | `generated/heiscore_lcd_engine.sv`           | `ims-arcade`                            |
| `DUT_ARCADE_SRCS` | `generated/heiscore_arcade_engine.sv`        | `ims-arcade-pong`                       |

The engines each carry their own copy of the `nortl_*` library modules, so a
board must pick exactly one of them.

The default board is the **Olimex GateMate EVB** (Cologne Chip CCGM1A1: Yosys
`synth_gatemate` → `nextpnr-himbaechel` → `gmpack`, flashed with
openFPGALoader). `olimex_gatemate_top.sv` drives the engine directly rather than
through the pin wrapper: a 10 MHz board oscillator feeds `pll_10_to_25` for the
25 MHz pixel clock, and the engine's 1-bit colour channels are replicated across
each 4-bit VGA channel of the resistor ladder. `ims-arcade` is the same board
with the IMS Arcade hat, driving its ILI9341 panel from the LCD engine.

`ims-arcade-pong` is the playable one: the same hat, with Pong on the VGA output
and the panel at the same time. Its engine holds one scene and two sinks — the
VGA generator walks the 640x480 master space, the LCD controller walks the
panel's 320x240 raster through a `Viewport` that halves both axes.

## Show Available Targets

The default Make target is `help`, so running `make` prints usage and all
available targets with short descriptions.

```sh
make
make help
```

## Clean

Remove generated files:

```sh
make clean
```

## Synthesis

Run technology-mapped synthesis for the board's FPGA architecture (the
Yosys `synth_*` pass comes from its `arch/<arch>.mk`):

```sh
make synthesis
```

Generate a generic synthesis netlist and Yosys graph:

```sh
make synthesis_generic
```

## Place-and-Route

Run place-and-route with nextpnr:

```sh
make pr
```

## Bitstream Generation and Flash

Generate a bitstream:

```sh
make gen_bitstream
```

Load or flash the generated bitstream:

```sh
make load_bitstream    # into SRAM, lost on power cycle
make flash_bitstream   # into the board's flash, survives a power cycle (useful for e.g. demo showcases)
```

> [!NOTE]
> Neither target is part of `make all`, by design.
> Use them explicitly when you want to program the FPGA.
> Each board's Makefile sets `LOAD_CMD`/`FLASH_CMD` to whatever that board
> needs: `openFPGALoader` for most boards, `iceprog` for the iCEBreaker
> (`openFPGALoader` has no dedicated iCEBreaker board profile), and
> `dfu-util` for the pico-ice, which has no `openFPGALoader` profile either.

## Convert to Verilog

Convert the SystemVerilog top module to Verilog:

```sh
make convert
```

## Build All

Run the full FPGA flow target from the Makefile:

```sh
make all
```

The current `all` recipe executes these steps in order:

1. `make clean`
2. `make synthesis`
3. `make pr`
4. `make gen_bitstream`

This ensures stale artifacts from previous runs are removed before a fresh
build.

> [!NOTE]
> `make all` intentionally stops after bitstream generation and does not
> call `load_bitstream` or `flash_bitstream`.
