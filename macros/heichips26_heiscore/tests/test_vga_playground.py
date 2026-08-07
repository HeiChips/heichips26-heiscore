import subprocess
from pathlib import Path

from nortl import Engine

from heiscore.core.vga import VGA
from heiscore import assemble_pong

def test_vga_playground():
    e = Engine('my_engine')

    p1_up = e.define_input("p1_up")
    p2_up = e.define_input("p2_up")
    p1_dn = e.define_input("p1_dn")
    p2_dn = e.define_input("p2_dn")


    pong = assemble_pong(e, p1_up, p1_dn, p2_up, p2_dn)

    vga_display = VGA(e, pong)

    with e.fork('VGA_interface'):
        vga_display.run()

    with open(Path(__file__).parent / 'artifacts/vga_playground/vga_playground_wrapper.sv') as fptr:
        wrapper_sv = fptr.read()

    outfile = Path(__file__).parent / 'artifacts/vga_playground/rendered.sv'

    with open(outfile, 'w') as fptr:
        fptr.write(wrapper_sv)
        fptr.write('\n' * 5)
        fptr.write(e.to_verilog())

    subprocess.run(['sv2v', outfile, '-w', 'adjacent'], check=False)
