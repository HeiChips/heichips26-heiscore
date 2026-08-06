from nortl import Engine
from nortl.core.protocols import Operand

from heiscore.core.objects import Box, GraphicsObject


class Paddle(Box):
    def __init__(self, engine: Engine, xpos: int, ypos: Operand, name: str):
        lx = xpos
        ux = xpos + 8
        ly = ypos
        uy = ypos + 24

        super().__init__(engine, lx, ly, ux, uy, 7)

    def solid(self, x: Operand, y: Operand):
        return self.visible(x, y)
