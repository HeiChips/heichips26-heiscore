import subprocess
from pathlib import Path

from nortl import Engine

from heiscore.core.objects import Box, GraphicsStash
from heiscore.core.vga import VGA


def test_vga_playground():
    e = Engine('my_engine')

    graphics = GraphicsStash(e)

    b1 = Box(e, 20, 20, 50, 50, 0x5)
    b2 = Box(e, 30, 30, 60, 70, 0x2)
    b3 = Box(e, 40, 40, 80, 80, 0x2)

    graphics.register(b1)
    graphics.register(b2)
    graphics.register(b3)

    display = VGA(e, graphics)
    display.run()

    with open(Path(__file__).parent / 'artifacts/vga_playground/vga_playground_wrapper.sv') as fptr:
        wrapper_sv = fptr.read()

    outfile = Path(__file__).parent / 'artifacts/vga_playground/rendered.sv'

    with open(outfile, 'w') as fptr:
        fptr.write(wrapper_sv)
        fptr.write('\n' * 5)
        fptr.write(e.to_verilog())

    subprocess.run(['sv2v', outfile, '-w', 'adjacent'], check=False)
