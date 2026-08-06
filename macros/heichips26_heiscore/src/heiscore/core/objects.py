from nortl import All, Any, Const, Engine, IfThenElse
from nortl.core.protocols import Operand, Renderable


class GraphicsObject:
    """Base class for objects on screen.

    The PPU itself is expected to query (x,y) coordinates to check if
    the object is on screen, which color it has and if there can be a collision
    """

    def __init__(self, engine: Engine) -> Renderable:
        self.engine = engine
        self._type = Const(0, 4)  # Obj Type

    def visible(self, x: Operand, y: Operand) -> Renderable:
        pass

    def color(self, x: Operand, y: Operand) -> Renderable:
        pass

    def solid(self, x: Operand, y: Operand) -> Renderable:
        pass

    def tick(self) -> None:
        """State update for a time step."""

    def type(self, x: Operand, y: Operand) -> Renderable:
        return IfThenElse(self.visible(x, y), self._type, Const(0, 4))


class GraphicsStash(GraphicsObject):
    """Group of graphics objects that expose the same interface."""

    def __init__(self, engine: Engine) -> Renderable:
        super().__init__(engine)

        self.graphics: list[GraphicsObject] = []

    def register(self, go: GraphicsObject) -> None:
        self.graphics.append(go)

    def visible(self, x: Operand, y: Operand) -> Renderable:
        list_of_visibilities = [go.visible(x, y) for go in self.graphics]
        return Any(*list_of_visibilities)

    def solid(self, x: Operand, y: Operand) -> Renderable:
        list_of_solids = [go.solid(x, y) for go in self.graphics]
        return Any(*list_of_solids)

    def color(self, x: Operand, y: Operand) -> Renderable:
        ret = Const(0)

        previous_visibilities = Const(False)

        for go in self.graphics:
            ret = IfThenElse(All(~previous_visibilities, go.visible(x, y)), go.color(x, y), ret)
            previous_visibilities = previous_visibilities | go.visible(x, y)

        return ret

    def type(self, x: Operand, y: Operand) -> Renderable:
        ret = Const(0)

        previous_visibilities = Const(False)

        for go in self.graphics:
            ret = IfThenElse(All(~previous_visibilities, go.visible(x, y)), go.type(x, y), ret)
            previous_visibilities = previous_visibilities | go.visible(x, y)

        return ret

    def tick(self) -> None:
        for go in self.graphics:  # FIXME: Maybe do in parallel Threads if necessary
            go.tick()


class Box(GraphicsObject):
    def __init__(self, engine: Engine, lx: Operand, ly: Operand, ux: Operand, uy: Operand, color: Operand, solid: Operand = Const(False)) -> None:
        super().__init__(engine)
        self.lx = lx
        self.ly = ly
        self.ux = ux
        self.uy = uy
        self.box_color = color
        self.solid = solid

    def visible(self, x: Operand, y: Operand) -> Renderable:
        return All(x >= self.lx, y >= self.ly, x < self.ux, y < self.uy)

    def color(self, x: Operand, y: Operand) -> Renderable:
        return IfThenElse(self.visible(x, y), self.box_color, Const(0))

    def solid(self, x: Operand, y: Operand) -> Renderable:
        return self.solid
