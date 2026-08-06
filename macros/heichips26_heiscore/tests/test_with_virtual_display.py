from nortl import Engine
from nortl.utils.test_wrapper import NoRTLTestBase

from heiscore.core.objects import Box, GraphicsStash
from heiscore.utils.virtual_display import VirtualDisplay


class TestSimple(NoRTLTestBase[Engine]):
    def init_sequence(self) -> Engine:
        return Engine('my_engine')

    def dut(self, e: Engine) -> None:
        pass

    def the_testbench(self, e: Engine) -> None:
        graphics = GraphicsStash(e)

        b1 = Box(e, 2, 2, 5, 5, 0x7)
        b2 = Box(e, 3, 3, 6, 7, 0x2)

        graphics.register(b1)
        graphics.register(b2)

        e.sync()

        vd = VirtualDisplay(e, 10, 10)
        vd.show(graphics)
