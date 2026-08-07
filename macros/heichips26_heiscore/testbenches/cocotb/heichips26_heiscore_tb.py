# SPDX-FileCopyrightText: 2026 XXX
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
#
# TODO: smoke test only. The macro is a 640x480@60 VGA source, so the real checks
# are the sync timings on uo_out (line length, hsync/vsync pulse widths, frame
# length). Until those are written, whole-frame checking lives in the Verilator
# harness under testbenches/verilator.

import os
import re
import logging
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, ClockCycles
from cocotb_tools.runner import get_runner

sim      = os.getenv("SIM", "icarus")
pdk_root = os.getenv("PDK_ROOT", Path("~/.ciel").expanduser())
pdk      = os.getenv("PDK", "ihp-sg13cmos5l")
scl      = os.getenv("SCL", "sg13cmos5l_stdcell")
# GL=1 selects the gate-level netlist; anything else (unset, "0", "") stays in RTL mode.
gl       = os.getenv("GL", "0").strip().lower() in ("1", "true", "yes", "on")

hdl_toplevel = "heichips26_heiscore"

CLK_FREQ_HZ      = 25e6  # pixel clock
CLK_FREQ_MHZ     = int(CLK_FREQ_HZ / 1e6)


async def start_clock(clock, freq=CLK_FREQ_MHZ):
    """Start the clock @ freq MHz"""
    period_ns = round(1 / freq * 1000, 4)
    c = Clock(clock, period_ns, "ns")
    cocotb.start_soon(c.start())


async def reset(reset, clock, cycles=2):
    """Pulse the active-low reset for `cycles` clock cycles."""
    cocotb.log.info("Reset asserted...")

    reset.value = 0
    await ClockCycles(clock, cycles)
    reset.value = 1
    await RisingEdge(clock)

    cocotb.log.info("Reset deasserted.")


async def start_up(dut):
    """Startup sequence: clock + reset. ui_in is unused by the macro."""
    await start_clock(dut.clk, CLK_FREQ_MHZ)
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await reset(dut.rst_n, dut.clk)


@cocotb.test()
async def test_reset_clears_heichips26_heiscore(dut):
    """After reset deasserts, uo_out must be zero."""
    logger = logging.getLogger("heichips26_heiscore_tb")

    logger.info("Startup sequence...")
    await start_up(dut)

    assert int(dut.uo_out.value) == 0, \
        f"uo_out not zero after reset (got {int(dut.uo_out.value)})"

    logger.info("Done!")


@cocotb.test()
async def test_outputs_stay_driven(dut):
    """Free-run for a couple of lines; uo_out must stay resolved."""
    logger = logging.getLogger("heichips26_heiscore_tb")

    logger.info("Startup sequence...")
    await start_up(dut)

    for _ in range(2000):
        await RisingEdge(dut.clk)
        await Timer(1, "ns")  # let combinational settle past edge
        assert dut.uo_out.value.is_resolvable, \
            f"uo_out has undriven bits (got {dut.uo_out.value})"

    logger.info("Done!")


def heichips26_heiscore_runner():

    proj_path = Path(__file__).resolve().parent

    sources  = []
    defines  = {}
    includes = [proj_path / "../../rtl/", proj_path / "../../rtl/generated/"]

    if gl:
        # SCL models
        sources.append(Path(pdk_root) / pdk / "libs.ref" / scl / "verilog" / f"{scl}.v")
        sources.append(Path(pdk_root) / pdk / "libs.ref" / scl / "verilog" / "sg13cmos5l_udp.v")

        # Unpowered gate-level netlist of the macro, as copied by `make copy-netlist`
        sources.append(proj_path / f"../../netlist/nl/{hdl_toplevel}.nl.v")

        # Unpowered netlist: USE_POWER_PINS must NOT be defined at all
        # (passing USE_POWER_PINS=False would still define the macro).
    else:
        # Pin wrapper plus the engine emitted by `make rtl` into rtl/generated/.
        sources.append(proj_path / "../../rtl/heichips26_heiscore.sv")
        sources.append(proj_path / "../../rtl/generated/heiscore_engine.sv")

    build_args = []

    if sim == "icarus":
        # -gno-specify: skip specify blocks; sg13cmos5l_stdcell.v uses
        # `ifnone with edge-sensitive paths`, which iverilog can't parse.
        build_args = ["-DSIM", "-gno-specify"]

    if sim == "verilator":
        # --preproc-token-limit: nortl flattens every state guard into one
        # expression, so a single line of the generated engine runs past
        # Verilator's default cap of 40k preprocessor tokens per line.
        build_args = [
            "--timing",
            "--trace",
            "--trace-fst",
            "--trace-structs",
            "--preproc-token-limit",
            "400000",
        ]

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        defines=defines,
        always=True,
        includes=includes,
        build_args=build_args,
        waves=True,
        timescale=("1ns", "1fs")
    )

    plusargs = []

    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module="heichips26_heiscore_tb",
        plusargs=plusargs,
        waves=True,
    )


if __name__ == "__main__":
    heichips26_heiscore_runner()
