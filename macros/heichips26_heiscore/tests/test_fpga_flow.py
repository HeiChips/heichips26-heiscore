import shutil
import subprocess

import pytest

from heiscore.top import MACRO_ROOT, emit

BOARD = 'olimex-gatemate'
TOOLS = ('make', 'yosys', 'nextpnr-himbaechel', 'gmpack')


def test_fpga_flow():
    """Emit the engine, then build the bitstream through the board Makefile."""
    for tool in TOOLS:
        if shutil.which(tool) is None:
            pytest.skip(f'{tool} is not on PATH; run inside nix develop')

    emit()

    subprocess.run(['make', '-C', str(MACRO_ROOT / 'fpga'), f'BOARD={BOARD}', 'gen_bitstream'], check=True)
