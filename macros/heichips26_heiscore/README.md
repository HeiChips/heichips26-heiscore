# HeiScore (ihp-sg13cmos5l)

<p align="center">
  <a href="final/render/heichips26_heiscore.png">
    <img src="final/render/heichips26_heiscore.png" alt="Render of the ihp-sg13cmos5l heichips26_heiscore layout" width=50%>
  </a>
  <br>
  <em>Render of the ihp-sg13cmos5l heichips26_heiscore layout.</em>
</p>

HeiScore brings Pong into silicone.
The design is not written in Verilog: it is described in Python with [nortl](https://pypi.org/project/nortl/) under [`src/heiscore/`](src/heiscore/) and emitted as SystemVerilog.

`src/heiscore/top.py` holds the single design definition everything else builds from.
The top-level `heichips26_heiscore` ([`rtl/heichips26_heiscore.sv`](rtl/heichips26_heiscore.sv)) is a hand-written pin wrapper implementing the standard chip interface (`ui_in`, `uo_out`, `uio_*`, `ena`, `clk`, `rst_n`) around that generated engine.

```
src/heiscore/  ── make rtl ──▶  rtl/generated/heiscore_engine.sv  ── make librelane ──▶  GDS
(committed)                     (build product, never committed)
```

`make rtl` emits `heiscore_engine.sv` and `heiscore_lcd_engine.sv` (FPGA-only) into `rtl/generated/`, which is git-ignored from the inside.
Every target that reads an engine (`lint-verilog`, `sim-rtl-*`, `librelane*`, `build-fpga`) regenerates it first if it is missing or stale, so a fresh clone needs no separate step.
However, it needs `nortl`, which the Nix devshell provides.
The two engines each carry their own copy of the `nortl_*` library modules, so they must never be read together; every consumer lists its sources explicitly instead of globbing `rtl/generated/*.sv`.

## Build Everything

```sh
make all
```

runs, in this order:

| #   | Target                  |                                                              |
| --- | ----------------------- | ------------------------------------------------------------ |
| 1   | `make rtl`              | Emit the engines from the nortl sources                      |
| 2   | `make lint-verilog-all` | Verilator lint                                               |
| 3   | `make build-fpga`       | FPGA bitstream (`BOARD=olimex-gatemate` by default)          |
| 4   | `make build-top`        | `librelane` → `copy-reports` → `copy-final` → `copy-netlist` |
| 5   | `make sim-all`          | `sim-rtl-verilog` → `sim-rtl-cocotb` → `sim-gl-cocotb`       |

Simulation runs _after_ the build so the gate-level simulation uses the netlists produced by this run.
A clean rebuild is:

```sh
make clean-all
make all
```

`make clean` removes all generated files (LibreLane runs, `final/`, `netlist/`, `verification/`, waveforms, generated RTL, FPGA outputs); sources and the LibreLane configuration stay untouched.
