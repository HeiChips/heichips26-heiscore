from nortl import Any, Concat, Const, Engine, IfThenElse, Volatile
from nortl.core.protocols import Renderable

from .core.lcd import LCD, MADCTL_LANDSCAPE_BGR
from .core.transform import Viewport
from .core.vga import VGA
from .music import MusicSequencerPWM
from .pong import Pong


def assemble_pong(e: Engine, p1_up: Renderable, p1_dn: Renderable, p2_up: Renderable, p2_dn: Renderable) -> Pong:
    paddle_pos1 = Volatile(e.define_scratch(9), 'identical_rw', 'exclusive_read')
    paddle_pos2 = Volatile(e.define_scratch(9), 'identical_rw', 'exclusive_read')

    start = Any(p1_dn, p1_up, p2_dn, p2_up)

    pong = Pong(e, paddle_pos1, paddle_pos2, start)

    timer = e.create_timer(24)

    e.sync()

    paddle_max_y = 420

    with e.fork('Paddle_handling'):  # noqa: SIM117
        pong.wait_for_start()

        with e.while_loop(Const(True)):
            timer.wait_delay(200000)

            with e.condition(p1_up):
                e.set(paddle_pos1, IfThenElse(paddle_pos1 < paddle_max_y, paddle_pos1 + 2, paddle_pos1))
            with e.condition(p1_dn):
                e.set(paddle_pos1, IfThenElse(paddle_pos1 > 10, paddle_pos1 - 2, paddle_pos1))
            with e.else_condition():
                pass

            e.sync()

            with e.condition(p2_up):
                e.set(paddle_pos2, IfThenElse(paddle_pos2 < paddle_max_y, paddle_pos2 + 2, paddle_pos2))
            with e.condition(p2_dn):
                e.set(paddle_pos2, IfThenElse(paddle_pos2 > 10, paddle_pos2 - 2, paddle_pos2))
            with e.else_condition():
                pass

            pong.tick()

    return pong


def define_keys(e: Engine) -> tuple:
    """Declare the arcade hat's key matrix ports and the four debounced paddle keys.

    The hat wires its keys as a 2x4 matrix: ``KEYS_X`` drives the two columns,
    ``KEYS_Y`` reads the four rows back, active low.
    """
    keys_x = e.define_output('KEYS_X', 2, 0)
    keys_y = e.define_input('KEYS_Y', 4)

    p1_up = Volatile(e.define_local('P1_UP', 1, 0), 'identical_rw')
    p2_up = Volatile(e.define_local('P2_UP', 1, 0), 'identical_rw')
    p1_dn = Volatile(e.define_local('P1_DN', 1, 0), 'identical_rw')
    p2_dn = Volatile(e.define_local('P2_DN', 1, 0), 'identical_rw')

    return keys_x, keys_y, p1_up, p1_dn, p2_up, p2_dn


def scan_keys(e: Engine, timer, keys_x, keys_y, p1_up, p1_dn, p2_up, p2_dn) -> None:
    """Body of the input handler: walk the two key columns forever.

    Each column is driven, given a settling delay, and then sampled. Call this
    inside a fork of its own -- it never returns.
    """
    with e.while_loop(Const(True)):
        e.set(keys_x, 0b10)
        timer.wait_delay(2000)
        e.set(p1_up, ~keys_y[1])
        e.set(p1_dn, ~keys_y[2])
        timer.wait_delay(2000)
        e.set(keys_x, 0b11)
        timer.wait_delay(2000)
        e.set(keys_x, 0b01)
        timer.wait_delay(2000)
        e.set(p2_up, ~keys_y[1])
        e.set(p2_dn, ~keys_y[0])
        timer.wait_delay(2000)


def make_music(e: Engine, start_music: Renderable):

    # Wait for the music

    music = MusicSequencerPWM(e, e.define_output('SPEAKER_PWM', 1, 0), 2)
    music.build_channels()
    with e.fork('music_input'):
        e.wait_for(Volatile(start_music, 'identical_rw', 'exclusive_read'))
        music.input_channels[0].send(Concat(Const(7, 4), music.tone_to_id['A']))
        music.input_channels[0].send(Concat(Const(1, 4), Const(0, 4)))
        music.input_channels[0].send(Concat(Const(7, 4), music.tone_to_id['A']))
        music.input_channels[0].send(Concat(Const(1, 4), Const(0, 4)))
        music.input_channels[0].send(Concat(Const(7, 4), music.tone_to_id['A']))
        music.input_channels[0].send(Concat(Const(1, 4), Const(0, 4)))
        music.input_channels[0].send(Concat(Const(6, 4), music.tone_to_id['F']))
        music.input_channels[0].send(Concat(Const(2, 4), music.tone_to_id['C2']))
        music.input_channels[0].send(Concat(Const(7, 4), music.tone_to_id['A']))
        music.input_channels[0].send(Concat(Const(1, 4), Const(0, 4)))
        music.input_channels[0].send(Concat(Const(6, 4), music.tone_to_id['F']))
        music.input_channels[0].send(Concat(Const(2, 4), music.tone_to_id['C2']))
        music.input_channels[0].send(Concat(Const(7, 4), music.tone_to_id['A']))
        music.input_channels[0].send(Concat(Const(1, 4), Const(0, 4)))
        music.input_channels[0].send(Concat(Const(16, 4), music.tone_to_id['A']))
        music.input_channels[0].send(Concat(Const(16, 4), Const(0, 4)))


def build_fpga() -> Engine:
    e = Engine('my_engine')

    keys_x, keys_y, p1_up, p1_dn, p2_up, p2_dn = define_keys(e)

    pong = assemble_pong(e, p1_up, p1_dn, p2_up, p2_dn)

    interlock_delay = e.create_timer()

    e.sync()

    vga_display = VGA(e, pong)

    with e.fork('VGA_interface'):
        vga_display.run()
    with e.fork('input_handler'):
        scan_keys(e, interlock_delay, keys_x, keys_y, p1_up, p1_dn, p2_up, p2_dn)

    start_music = e.define_local('start_music', 1, value=Any(p1_dn, p1_up, p2_dn, p2_up))
    make_music(e, start_music)

    return e


def build_arcade() -> Engine:
    """Playable Pong on the IMS Arcade hat, on the VGA output and the panel at once.

    One scene, three forks and two sinks: the VGA generator walks the 640x480
    master space directly, while the LCD controller walks the panel's 320x240
    raster through a :class:`~.core.transform.Viewport` that halves both axes.
    Both sample the same combinational scene, so only the paddle handler inside
    ``assemble_pong`` drives :meth:`Pong.tick` -- the panel's ~65 Hz frame rate
    runs free against the 60 Hz VGA output and neither sink owns the game clock.
    """
    e = Engine('heiscore_arcade_engine')

    keys_x, keys_y, p1_up, p1_dn, p2_up, p2_dn = define_keys(e)

    pong = assemble_pong(e, p1_up, p1_dn, p2_up, p2_dn)

    interlock_delay = e.create_timer()

    e.sync()

    vga_display = VGA(e, pong)
    lcd_display = LCD(e, Viewport(e, pong, scale=2), madctl=MADCTL_LANDSCAPE_BGR)

    with e.fork('VGA_interface'):
        vga_display.run()
    with e.fork('LCD_interface'):
        lcd_display.run()
    with e.fork('input_handler'):
        scan_keys(e, interlock_delay, keys_x, keys_y, p1_up, p1_dn, p2_up, p2_dn)

    start_music = e.define_local('start_music', 1, value=Any(p1_dn, p1_up, p2_dn, p2_up))
    make_music(e, start_music)

    return e
