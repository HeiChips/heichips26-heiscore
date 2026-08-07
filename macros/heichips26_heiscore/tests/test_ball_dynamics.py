from nortl import Const, Engine
from nortl.utils.test_wrapper import NoRTLTestBase

from heiscore.pong import Pong


class TestCollisionUpperLower(NoRTLTestBase[Engine]):
    def init_sequence(self) -> Engine:
        return Engine('my_engine')

    def dut(self, e: Engine) -> None:
        pass

    def the_testbench(self, e: Engine) -> None:
        pong = Pong(e, Const(200), Const(200), Const(0, 1))
        pong.construct_frame()

        # Make all walls reflective by setting type to 1
        for item in pong.graphics:
            item._type = Const(1, 4)

        pong.construct_ball(False)
        e.sync()
        pong.start_game()

        # Test collission to first wall

        with e.for_loop(50, 500, 10) as x:
            e.set(pong.ball.position[0], x)
            e.set(pong.ball.position[1], 20)

            e.set(pong.ball.velocity[0], 0)
            e.set(pong.ball.velocity[1], 1)

            e.set(pong.ball.direction[0], 0)
            e.set(pong.ball.direction[1], 1)

            with e.for_loop(0, 20) as steps:
                e.print(
                    'Step %0d, Ball @(%0d, %0d), Direction = (%0d, %0d)',
                    steps,
                    pong.ball.position[0],
                    pong.ball.position[1],
                    pong.ball.direction[0],
                    pong.ball.direction[1],
                )
                pong.tick()

            # Check that only the direction in Y has changed!
            self.assertEqual(pong.ball.direction[0], 0)
            self.assertEqual(pong.ball.direction[1], 0)

        self.reset_timeout()

        # Test collission to second wall

        with e.for_loop(50, 500, 10) as x:
            e.set(pong.ball.position[0], x)
            e.set(pong.ball.position[1], 460)

            e.set(pong.ball.velocity[0], 0)
            e.set(pong.ball.velocity[1], 1)

            e.set(pong.ball.direction[0], 0)
            e.set(pong.ball.direction[1], 0)

            with e.for_loop(0, 20) as steps:
                e.print(
                    'Step %0d, Ball @(%0d, %0d), Direction = (%0d, %0d)',
                    steps,
                    pong.ball.position[0],
                    pong.ball.position[1],
                    pong.ball.direction[0],
                    pong.ball.direction[1],
                )
                pong.ball.bbox()
                pong.tick()

            # Check that only the direction in Y has changed!
            self.assertEqual(pong.ball.direction[0], 0)
            self.assertEqual(pong.ball.direction[1], 1)

        e.sync()


class TestCollisionLeftRight(NoRTLTestBase[Engine]):
    def init_sequence(self) -> Engine:
        return Engine('my_engine')

    def dut(self, e: Engine) -> None:
        pass

    def the_testbench(self, e: Engine) -> None:
        pong = Pong(e, Const(200), Const(200), Const(0, 1))
        pong.construct_frame()

        # Make all walls reflective by setting type to 1
        for item in pong.graphics:
            item._type = Const(1, 4)

        pong.construct_ball(False)

        e.sync()
        pong.start_game()

        # Test collission to first wall

        with e.for_loop(50, 51) as y:
            e.set(pong.ball.position[0], 20)
            e.set(pong.ball.position[1], y)

            e.set(pong.ball.velocity[0], 1)
            e.set(pong.ball.velocity[1], 0)

            e.set(pong.ball.direction[0], 1)
            e.set(pong.ball.direction[1], 0)

            with e.for_loop(0, 20) as steps:
                e.print(
                    'Step %0d, Ball @(%0d, %0d), Direction = (%0d, %0d)',
                    steps,
                    pong.ball.position[0],
                    pong.ball.position[1],
                    pong.ball.direction[0],
                    pong.ball.direction[1],
                )
                pong.tick()

            # Check that only the direction in Y has changed!
            self.assertEqual(pong.ball.direction[0], 0)
            self.assertEqual(pong.ball.direction[1], 0)

        # Test collission to first wall

        with e.for_loop(50, 51) as y:
            e.set(pong.ball.position[0], 600)
            e.set(pong.ball.position[1], y)

            e.set(pong.ball.velocity[0], 1)
            e.set(pong.ball.velocity[1], 0)

            e.set(pong.ball.direction[0], 0)
            e.set(pong.ball.direction[1], 0)

            with e.for_loop(0, 20) as steps:
                e.print(
                    'Step %0d, Ball @(%0d, %0d), Direction = (%0d, %0d)',
                    steps,
                    pong.ball.position[0],
                    pong.ball.position[1],
                    pong.ball.direction[0],
                    pong.ball.direction[1],
                )
                pong.tick()

            # Check that only the direction in Y has changed!
            self.assertEqual(pong.ball.direction[0], 0)
            self.assertEqual(pong.ball.direction[1], 0)

        e.sync()
