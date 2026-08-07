"""The design definition, shared by the pytest flows, the LVS-VGA check and `make rtl`."""

from pathlib import Path

from nortl import Const, Engine

from heiscore import build_arcade
from heiscore.core.lcd import MADCTL_LANDSCAPE_BGR, LCD
from heiscore.core.objects import Box, GraphicsStash
from heiscore.core.transform import Viewport
from heiscore.core.vga import VGA
from heiscore.pong import Pong

ENGINE_NAME = 'heiscore_engine'
LCD_ENGINE_NAME = 'heiscore_lcd_engine'
ARCADE_ENGINE_NAME = 'heiscore_arcade_engine'

MACRO_ROOT = Path(__file__).resolve().parents[2]

GENERATED_DIR = Path('rtl') / 'generated'
RTL_PATH = GENERATED_DIR / f'{ENGINE_NAME}.sv'
LCD_RTL_PATH = GENERATED_DIR / f'{LCD_ENGINE_NAME}.sv'
ARCADE_RTL_PATH = GENERATED_DIR / f'{ARCADE_ENGINE_NAME}.sv'


def build() -> Engine:
    """The VGA design that gets taped out."""
    engine = Engine(ENGINE_NAME)

    pong = Pong(engine, Const(0), Const(0), Const(1))
    timer = engine.create_timer()

    with engine.fork("display_thread"):
        VGA(engine, pong).run()

    with engine.fork("main_loop"):
        with engine.while_loop(Const(True)):
            timer.wait_delay(20000)
            pong.tick()


    return engine


def build_lcd() -> Engine:
    """The ILI9341 variant. The scene stays in 640x480 master space; the viewport halves both axes."""
    engine = Engine(LCD_ENGINE_NAME)

    graphics = GraphicsStash(engine)
    graphics.register(Box(engine, 40, 40, 100, 100, 0x5))
    graphics.register(Box(engine, 60, 60, 120, 140, 0x2))
    graphics.register(Box(engine, 80, 80, 160, 160, 0x2))

    view = Viewport(engine, graphics, scale=2)

    LCD(engine, view, madctl=MADCTL_LANDSCAPE_BGR).run()

    return engine


def emit(outfile: Path | None = None) -> Path:
    """Write the generated engine to `outfile` (default: `rtl/`)."""
    return _write(build(), outfile or MACRO_ROOT / RTL_PATH)


def emit_lcd(outfile: Path | None = None) -> Path:
    """Write the generated LCD engine to `outfile` (default: `rtl/`)."""
    return _write(build_lcd(), outfile or MACRO_ROOT / LCD_RTL_PATH)


def emit_arcade(outfile: Path | None = None) -> Path:
    """Write the generated arcade engine to `outfile` (default: `rtl/`)."""
    return _write(build_arcade(), outfile or MACRO_ROOT / ARCADE_RTL_PATH)


def _write(engine: Engine, outfile: Path) -> Path:
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(engine.to_verilog())

    return outfile


# The variants `main()` can emit. The default is the VGA design that gets taped out.
VARIANTS = {'lcd': emit_lcd, 'arcade': emit_arcade}


def main() -> None:
    """`python -m heiscore.top [lcd|arcade] [outfile]`, used by `make rtl` and `make check-rtl`."""
    import sys

    args = sys.argv[1:]

    variant = VARIANTS.get(args[0]) if args else None
    if variant is not None:
        args = args[1:]

    outfile = Path(args[0]) if args else None

    print((variant or emit)(outfile))


if __name__ == '__main__':
    main()
