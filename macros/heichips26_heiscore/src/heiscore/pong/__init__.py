from nortl import Any, Engine, Volatile
from nortl.core.protocols import Renderable

from heiscore.core.objects import Box, GraphicsStash

from .objects import Ball, Paddle, Score


class Pong(GraphicsStash):
    def __init__(self, engine: Engine, pos_paddle_1: Renderable, pos_paddle_2: Renderable, start: Renderable) -> None:
        super().__init__(engine)

        self.pos_paddle_1 = pos_paddle_1
        self.pos_paddle_2 = pos_paddle_2
        self.start = start

        self.engine.sync()

        self.construct_frame()
        self.construct_paddles()
        self.construct_score()
        self.construct_ball()

    def construct_frame(self) -> None:
        size_x = 640
        size_y = 480

        frame_list = [
            Box(self.engine, 0, 0, size_x, 10, 7, type=1),
            Box(self.engine, 0, size_y - 10, size_x, size_y, 7, type=1),
            Box(self.engine, size_x - 10, 0, size_x, size_y, 5, type=3),  # right
            Box(self.engine, 0, 0, 10, size_y, 1, type=4),  # left
        ]

        for item in frame_list:
            self.register(item)

    def construct_paddles(self) -> None:
        self.register(Paddle(self.engine, 50, Volatile(self.pos_paddle_1, 'identical_rw', 'exclusive_read'), 'paddle_1'))
        self.register(Paddle(self.engine, 580, Volatile(self.pos_paddle_2, 'identical_rw', 'exclusive_read'), 'paddle_2'))

    def construct_score(self) -> None:
        self.score_1 = Score(self.engine, 100, 40)
        self.score_2 = Score(self.engine, 640 - 100 - 76, 40)

        self.register(self.score_1)
        self.register(self.score_2)

        self.engine.sync()

        self.score_1.set_value(0)
        self.score_2.set_value(0)

    def construct_ball(self) -> None:
        self.ball = Ball(self.engine, self)
        self.register(self.ball)
        self.initialize_ball_position()

        def cb_player1_points(collided):
            with self.engine.condition(collided == 3):
                self.score_1.set_value(self.score_1.get_value() + 1)
                self.initialize_ball_position()
                # self.wait_for_start()
            with self.engine.else_condition():
                pass
            self.engine.sync()

        def cb_player2_points(collided):
            with self.engine.condition(collided == 4):
                self.score_2.set_value(self.score_2.get_value() + 1)
                self.initialize_ball_position()
                # self.wait_for_start()
            with self.engine.else_condition():
                pass
            self.engine.sync()

        def cb_end_of_game(collided):
            with self.engine.condition(Any(self.score_1.get_value() == 0xA, self.score_2.get_value() == 0xA)):
                self.score_1.set_value(0)
                self.score_2.set_value(0)
                self.wait_for_start()
            with self.engine.else_condition():
                pass

        self.ball.collision_callbacks.append(cb_player1_points)
        self.ball.collision_callbacks.append(cb_player2_points)
        self.ball.collision_callbacks.append(cb_end_of_game)

    def initialize_ball_position(self) -> None:
        self.engine.set(self.ball.position[0], 640 // 2)
        self.engine.set(self.ball.position[1], 480 // 2)

        self.engine.set(self.ball.velocity[0], 1)
        self.engine.set(self.ball.velocity[1], 1)

    def wait_for_start(self) -> None:
        self.engine.wait_for(self.start)
        self.start_game()
        self.engine.sync()

    def start_game(self) -> None:
        self.engine.set(self.ball.running, 1)

    def pause_game(self) -> None:
        self.engine.set(self.ball.running, 0)
