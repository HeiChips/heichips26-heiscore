from nortl import Engine
from nortl.core.protocols import Renderable

from heiscore.core.objects import Box, GraphicsStash


class Pong(GraphicsStash):
    def __init__(self, engine: Engine, paddle_1: Renderable, paddle_2: Renderable) -> None:
        super().__init__(engine)

        self.paddle_1 = paddle_1
        self.paddle_2 = paddle_2

    def construct_frame(self):
        size_x = 640
        size_y = 480

        frame_list = [
            Box(self.engine, 0, 0, size_x, 10, 7),
            Box(self.engine, 0, size_y - 10, size_x, size_y, 7),
            Box(self.engine, size_x - 10, 0, size_x, size_y, 7),
            Box(self.engine, 0, 0, 10, size_y, 7),
        ]

        for item in frame_list:
            self.register(item)
