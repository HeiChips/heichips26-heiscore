from nortl import All, Any, Const, Engine, IfThenElse, Volatile
from nortl.core.protocols import Operand, Renderable

from heiscore.core.objects import Box, GraphicsObject, GraphicsStash


class Paddle(Box):
    def __init__(self, engine: Engine, xpos: int, ypos: Operand, name: str) -> None:
        lx = xpos
        ux = xpos + 8
        ly = ypos
        uy = ypos + 48

        super().__init__(engine, lx, ly, ux, uy, 4)

        self._type = 2

    def solid(self, x: Operand, y: Operand) -> Renderable:
        return self.visible(x, y)


class DisplaySegment(Box):
    def __init__(self, engine: Engine, hv: bool, xpos: int, ypos: Operand) -> None:

        if hv:
            lx = xpos
            ux = xpos + 24
            ly = ypos
            uy = ypos + 8
        else:
            lx = xpos
            ux = xpos + 8
            ly = ypos
            uy = ypos + 24

        self.enabled = Volatile(engine.define_scratch(1), 'identical_rw', 'exclusive_read')
        engine.set(self.enabled, 0)

        super().__init__(engine, lx, ly, ux, uy, 2)

    def visible(self, x: Operand, y: Operand) -> Renderable:
        return super().visible(x, y) & self.enabled


class Score(GraphicsStash):
    def __init__(
        self,
        engine: Engine,
        xpos: Operand,
        ypos: Operand,
    ) -> None:
        super().__init__(engine)

        self.segments: dict[str, DisplaySegment] = {}

        self.segments['A'] = DisplaySegment(engine, True, xpos + 10, ypos + 0)
        self.segments['B'] = DisplaySegment(engine, False, xpos + 36, ypos + 10)
        self.segments['C'] = DisplaySegment(engine, False, xpos + 36, ypos + 46)
        self.segments['D'] = DisplaySegment(engine, True, xpos + 10, ypos + 70)
        self.segments['E'] = DisplaySegment(engine, False, xpos, ypos + 46)
        self.segments['F'] = DisplaySegment(engine, False, xpos, ypos + 10)
        self.segments['G'] = DisplaySegment(engine, True, xpos + 10, ypos + 36)

        for item in self.segments.values():
            self.register(item)

        self.value = self.engine.define_scratch(4)
        self.engine.set(self.value, 0)

    def set_value(self, new_value: Operand):
        truth_table = {
            0x0: {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 0},
            0x1: {'A': 0, 'B': 1, 'C': 1, 'D': 0, 'E': 0, 'F': 0, 'G': 0},
            0x2: {'A': 1, 'B': 1, 'C': 0, 'D': 1, 'E': 1, 'F': 0, 'G': 1},
            0x3: {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 0, 'F': 0, 'G': 1},
            0x4: {'A': 0, 'B': 1, 'C': 1, 'D': 0, 'E': 0, 'F': 1, 'G': 1},
            0x5: {'A': 1, 'B': 0, 'C': 1, 'D': 1, 'E': 0, 'F': 1, 'G': 1},
            0x6: {'A': 1, 'B': 0, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 1},
            0x7: {'A': 1, 'B': 1, 'C': 1, 'D': 0, 'E': 0, 'F': 0, 'G': 0},
            0x8: {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 1},
            0x9: {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 0, 'F': 1, 'G': 1},
            0xA: {'A': 1, 'B': 1, 'C': 1, 'D': 0, 'E': 1, 'F': 1, 'G': 1},
            0xB: {'A': 0, 'B': 0, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 1},
            0xC: {'A': 0, 'B': 0, 'C': 0, 'D': 1, 'E': 1, 'F': 0, 'G': 1},
            0xD: {'A': 0, 'B': 1, 'C': 1, 'D': 1, 'E': 1, 'F': 0, 'G': 1},
            0xE: {'A': 1, 'B': 0, 'C': 0, 'D': 1, 'E': 1, 'F': 1, 'G': 1},
            0xF: {'A': 1, 'B': 0, 'C': 0, 'D': 0, 'E': 1, 'F': 1, 'G': 1},
        }

        for k, segment in self.segments.items():
            value = Const(truth_table[0][k], 4)
            for i in range(16):
                value = IfThenElse(new_value == Const(i), truth_table[i][k], value)
            self.engine.set(segment.enabled, value)

        self.engine.set(self.value, new_value)

    def get_value(self) -> Renderable:
        return self.value


class Ball(GraphicsObject):
    ball_bitmap = [  # noqa: RUF012
        [0,0,0,0,3,3,0,0,0,0],
        [0,0,5,4,3,3,4,5,0,0],
        [0,5,4,2,3,3,2,4,5,0],
        [0,4,2,2,3,3,2,2,4,0],
        [3,3,3,3,3,3,3,3,3,3],
        [3,3,3,3,3,3,3,3,3,3],
        [0,4,2,2,3,3,2,2,4,0],
        [0,5,4,2,3,3,2,4,5,0],
        [0,0,5,4,3,3,4,5,0,0],
        [0,0,0,0,3,3,0,0,0,0],
    ]


    def __init__(self, engine: Engine, all_objects: GraphicsStash):
        super().__init__(engine)

        self.all_objects = all_objects

        self.velocity = [Volatile(self.engine.define_scratch(4), 'identical_rw'), Volatile(self.engine.define_scratch(4), 'identical_rw')]
        self.direction = [Volatile(self.engine.define_scratch(1), 'identical_rw'), Volatile(self.engine.define_scratch(1), 'identical_rw')]
        self.position = [
            Volatile(self.engine.define_scratch(10), 'identical_rw', 'exclusive_read'),
            Volatile(self.engine.define_scratch(10), 'identical_rw', 'exclusive_read'),
        ]

        self.half_size = Const(5, 9)

        self.lx = self.position[0] - self.half_size
        self.ly = self.position[1] - self.half_size
        self.ux = self.position[0] + self.half_size
        self.uy = self.position[1] + self.half_size

        self.collision_callbacks = []

        self.running = self.engine.define_scratch(1)
        self.engine.set(self.running, 0)

    def color(self, x: Operand, y: Operand) -> Renderable:
        # return IfThenElse(All(x >= self.lx, y >= self.ly, x < self.ux, y < self.uy), 3, 0)


        color = Const(0,4)
        for i in range(10):
            for j in range(10):
                color=IfThenElse(All(self.half_size + x - self.position[0]==i, self.half_size + y - self.position[1]==j), self.ball_bitmap[i][j], color)

        return color

    def visible(self, x: Operand, y: Operand) -> Renderable:
        return All(x >= self.lx, y >= self.ly, x < self.ux, y < self.uy)

    def bbox(self) -> None:

        self.engine.print('Ball BBox = (%0d, %0d), (%0d, %0d)', self.lx, self.ly, self.ux, self.uy)

    def tick(self)-> None:
        with self.engine.condition(self.running):
            self.mechanics()
        with self.engine.else_condition():
            pass

    def mechanics(self) -> None:
        self.engine.set(self.position[0], IfThenElse(self.direction[0], self.position[0] - self.velocity[0], self.position[0] + self.velocity[0]))
        self.engine.set(self.position[1], IfThenElse(self.direction[1], self.position[1] - self.velocity[1], self.position[1] + self.velocity[1]))

        self.engine.sync()

        # R Anstoßen
        rtype = self.all_objects.type(self.position[0] + self.half_size, self.position[1])
        rcollide = Any(
            All(
                rtype != 0,
                self.direction[1] == 0,
            ),
        )
        # L Anstoßen
        ltype = self.all_objects.type(self.position[0] - self.half_size, self.position[1])
        lcollide = Any(
            All(
                ltype != 0,
                self.direction[1] == 1,
            ),
        )

        # Oben Anstoßen
        otype = self.all_objects.type(self.position[0], self.position[1] + self.half_size)
        ocollide = Any(
            All(
                otype != 0,
                self.direction[1] == 0,
            ),
        )
        # Unten Anstoßen
        utype = self.all_objects.type(self.position[0], self.position[1] - self.half_size)
        ucollide = Any(
            All(
                utype != 0,
                self.direction[1] == 1,
            ),
        )

        with self.engine.condition(rcollide):
            self.engine.set(self.direction[0], ~self.direction[0])
            for cb in self.collision_callbacks:
                cb(rtype)
        with self.engine.condition(lcollide):
            self.engine.set(self.direction[0], ~self.direction[0])
            for cb in self.collision_callbacks:
                cb(ltype)
        with self.engine.else_condition():
            pass

        self.engine.sync()

        with self.engine.condition(ucollide):
            self.engine.set(self.direction[1], ~self.direction[1])
            for cb in self.collision_callbacks:
                cb(utype)
        with self.engine.condition(ocollide):
            self.engine.set(self.direction[1], ~self.direction[1])
            for cb in self.collision_callbacks:
                cb(otype)
        with self.engine.else_condition():
            pass
