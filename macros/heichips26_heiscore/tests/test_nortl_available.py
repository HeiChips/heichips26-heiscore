from nortl import Engine
from nortl.utils.test_wrapper import NoRTLTestBase


class TestSimple(NoRTLTestBase[Engine]):
    def init_sequence(self) -> Engine:
        return Engine("my_engine")

    def dut(self, e: Engine) -> None:
        pass

    def the_testbench(self, e: Engine) -> None:
        e.sync()
