from nortl import Concat, Engine
from nortl.core.protocols import Operand, Renderable

from .objects import GraphicsObject
from .vga import H_VISIBLE_AREA, V_VISIBLE_AREA


def _key(coordinate: Operand) -> str:
    """Stable dict key for a coordinate expression.
    """
    render = getattr(coordinate, 'render', None)
    return render() if render is not None else repr(coordinate)


class Viewport(GraphicsObject):
    """Presents a source scene in a different coordinate space.

    Every sink in this design -- the VGA generator, the LCD controller -- walks
    its own raster and asks the scene for the colour at each position. The scene
    itself is written once, in the master coordinate space, which is the
    640x480 VGA visible area. A ``Viewport`` sits between a sink and the scene
    and rewrites the sink's raster position into that master space, so a panel
    with a different size or orientation shows the same picture without the
    game objects knowing about it.

    The mapping is destination -> source, because that is the direction a
    combinational pixel source is queried in. It is pure wiring plus at most one
    subtraction per axis: no line buffer, no frame buffer, no extra clock.

    Arguments:
        engine: The engine the expressions are built in.
        source: The scene in master coordinates.
        scale: How many source pixels one destination pixel covers, per axis.
            ``2`` turns the 640x480 master into a 320x240 destination. Powers of
            two become a concatenation with zero bits, i.e. free.
        rotate: Clockwise rotation of the image, in degrees. One of 0, 90, 180,
            270. A quarter turn swaps the destination's width and height.
        mirror_x: Mirror the destination raster left to right.
        mirror_y: Mirror the destination raster top to bottom.
        src_width: Width of the master space. Defaults to the VGA visible area.
        src_height: Height of the master space. Defaults to the VGA visible area.

    !!! note

        Downscaling is decimation, not averaging: with one bit per channel there
        is nothing to average. A ``scale`` of 2 therefore drops every other
        source pixel, and a feature thinner than ``scale`` may vanish depending
        on where it sits. Keep the smallest object in the scene at least
        ``scale`` pixels wide in the master space.
    """

    def __init__(
        self,
        engine: Engine,
        source: GraphicsObject,
        scale: int = 1,
        rotate: int = 0,
        mirror_x: bool = False,
        mirror_y: bool = False,
        src_width: int = H_VISIBLE_AREA,
        src_height: int = V_VISIBLE_AREA,
    ) -> None:
        super().__init__(engine)

        if rotate not in (0, 90, 180, 270):
            raise ValueError(f'rotate must be one of 0, 90, 180, 270, got {rotate}')
        if scale < 1:
            raise ValueError(f'scale must be at least 1, got {scale}')

        self.source = source
        self.scale = scale
        self.rotate = rotate
        self.mirror_x = mirror_x
        self.mirror_y = mirror_y
        self.src_width = src_width
        self.src_height = src_height

        self._quarter_turn = rotate in (90, 270)

        self._mapped: dict[tuple[str, str], tuple[Operand, Operand]] = {}

    # --- Destination geometry --------------------------------------------

    @property
    def width(self) -> int:
        """Width of the destination raster this viewport can serve."""
        return (self.src_height if self._quarter_turn else self.src_width) // self.scale

    @property
    def height(self) -> int:
        """Height of the destination raster this viewport can serve."""
        return (self.src_width if self._quarter_turn else self.src_height) // self.scale

    # --- Coordinate mapping ----------------------------------------------

    def _stretch(self, coordinate: Operand) -> Operand:
        """Scale a destination coordinate up into master units."""
        if self.scale == 1:
            return coordinate

        shift = self.scale.bit_length() - 1
        if (1 << shift) == self.scale and hasattr(coordinate, 'render'):
            return Concat(coordinate, '0b' + '0' * shift)

        return coordinate * self.scale

    def _map(self, x: Operand, y: Operand) -> tuple[Operand, Operand]:
        """Rewrite a destination position into the master coordinate space."""
        key = (_key(x), _key(y))
        if key in self._mapped:
            return self._mapped[key]

        if self.mirror_x:
            x = (self.width - 1) - x
        if self.mirror_y:
            y = (self.height - 1) - y

        u = self._stretch(x)
        v = self._stretch(y)

        if self.rotate == 0:
            mapped = (u, v)
        elif self.rotate == 90:
            mapped = (v, (self.src_height - 1) - u)
        elif self.rotate == 180:
            mapped = ((self.src_width - 1) - u, (self.src_height - 1) - v)
        else:
            mapped = ((self.src_width - 1) - v, u)

        self._mapped[key] = mapped
        return mapped

    # --- GraphicsObject interface ----------------------------------------

    def visible(self, x: Operand, y: Operand) -> Renderable:
        return self.source.visible(*self._map(x, y))

    def color(self, x: Operand, y: Operand) -> Renderable:
        return self.source.color(*self._map(x, y))

    def solid(self, x: Operand, y: Operand) -> Renderable:
        return self.source.solid(*self._map(x, y))

    def type(self, x: Operand, y: Operand) -> Renderable:
        return self.source.type(*self._map(x, y))

    def tick(self) -> None:
        # A viewport is a view, not a copy: whoever owns the master timing ticks
        # the scene. Forwarding here would advance the game once per sink.
        pass
