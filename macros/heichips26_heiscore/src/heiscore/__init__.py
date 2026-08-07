from nortl import Const, Engine, IfThenElse, Volatile, Any
from nortl.core.protocols import Renderable

from .core.vga import VGA
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


def build_fpga() -> Engine:
    e = Engine('my_engine')

    keys_x = e.define_output('KEYS_X', 2, 0)
    keys_y = e.define_input('KEYS_Y', 4)

    p1_up = Volatile(e.define_local('P1_UP', 1, 0), 'identical_rw')
    p2_up = Volatile(e.define_local('P2_UP', 1, 0), 'identical_rw')
    p1_dn = Volatile(e.define_local('P1_DN', 1, 0), 'identical_rw')
    p2_dn = Volatile(e.define_local('P2_DN', 1, 0), 'identical_rw')


    pong = assemble_pong(e, p1_up, p1_dn, p2_up, p2_dn)

    interlock_delay = e.create_timer()

    e.sync()

    vga_display = VGA(e, pong)


    with e.fork('VGA_interface'):
        vga_display.run()
    with e.fork('input_handler'):  # noqa: SIM117
        with e.while_loop(Const(True)):
            e.set(keys_x, 0b10)
            interlock_delay.wait_delay(2000)
            e.set(p1_up, ~keys_y[1])
            e.set(p1_dn, ~keys_y[2])
            interlock_delay.wait_delay(2000)
            e.set(keys_x, 0b11)
            interlock_delay.wait_delay(2000)
            e.set(keys_x, 0b01)
            interlock_delay.wait_delay(2000)
            e.set(p2_up, ~keys_y[1])
            e.set(p2_dn, ~keys_y[0])
            interlock_delay.wait_delay(2000)


    return e
