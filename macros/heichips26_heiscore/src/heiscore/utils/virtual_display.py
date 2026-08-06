from nortl import Const, Engine, IfThenElse

from ..core.objects import GraphicsStash


class VirtualDisplay:
    def __init__(self, e: Engine, size_x: int, size_y: int):
        self.engine = e
        self.size_x = size_x
        self.size_y = size_y

    def show(self, go: GraphicsStash):
        self.engine.print('\033[2J')

        for y in range(self.size_y):
            # Get color of pixel, is assumed to be color[2:0] = (RGB)
            pixels_x = [go.color(x, y) for x in range(self.size_x)]

            red = [IfThenElse((pix & 0b100) != 0, Const(255, 8), 0) for pix in pixels_x]
            green = [IfThenElse((pix & 0b010) != 0, Const(255, 8), 0) for pix in pixels_x]
            blue = [IfThenElse((pix & 0b001) != 0, Const(255, 8), 0) for pix in pixels_x]

            pixstr = '\033[48;2;%0d;%0d;%0dm..'
            return_to_top = '\033[0;0H'
            move_to_pix_position = '\033[%0d;%0dH'

            # Create a list of values (x,y,r,g,b)

            printlst = []

            for x, r, g, b in zip(range(self.size_x), red, green, blue):
                printlst.append(y)
                printlst.append(x + 20)
                printlst.append(r)
                printlst.append(g)
                printlst.append(b)

            # Assemble print string

            item = f'{move_to_pix_position}{pixstr}{return_to_top}'

            self.engine.print('Line: ' + item * self.size_x, *printlst)
