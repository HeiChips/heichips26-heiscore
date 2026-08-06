import subprocess
from pathlib import Path

from nortl import Const, Engine, IfThenElse, Volatile

from heiscore import build_fpga
from heiscore.core.vga import VGA


def test_fpga_flow():
    e = build_fpga()

    outfile = Path(__file__).parent / 'artifacts/fpga/rendered.sv'

    with open(outfile, 'w') as fptr:
        fptr.write(e.to_verilog())

    # Yosys step
    subprocess.run(['yosys', '-s', 'synthesize.ys'], cwd=Path(__file__).parent / 'artifacts/fpga', check=False)

    # PnR
    subprocess.run(
        [
            'nextpnr-himbaechel',
            '--device=CCGM1A1',
            '--json',
            'gatemate_wrapper_yosys.json',
            '-o',
            'ccf=gatemate_constraints.ccf',
            '-o',
            'out=impl.txt',
            '--router',
            'router2',
        ],
        cwd=Path(__file__).parent / 'artifacts/fpga',
        check=False,
    )

    # Generate Bitstream
    subprocess.run(
        ['gmpack', 'impl.txt', 'gatemate_wrapper.bit'],
        cwd=Path(__file__).parent / 'artifacts/fpga',
        check=False,
    )

    # Write bitstream to FPGA

    subprocess.run(
        [
            'openFPGALoader',
            '-c',
            'dirtyJtag',
            'gatemate_wrapper.bit',
        ],
        cwd=Path(__file__).parent / 'artifacts/fpga',
        check=False,
    )
