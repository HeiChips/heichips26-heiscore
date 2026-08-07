from nortl import Concat, Const, Engine, IfThenElse

from .objects import GraphicsStash

# --- Panel geometry -------------------------------------------------------
# ILI9341 in its native portrait orientation. The scan order the controller
# actually uses follows from MADCTL, see ``LCD.h_pixels`` / ``LCD.v_pixels``.
NATIVE_H_PIXELS = 240
NATIVE_V_PIXELS = 320

# --- Clocking -------------------------------------------------------------
CLOCK_HZ = 25_000_000

# --- ILI9341 command set (datasheet chapter 8) ----------------------------
CMD_SWRESET = 0x01
CMD_SLPOUT = 0x11
CMD_DISPON = 0x29
CMD_CASET = 0x2A
CMD_PASET = 0x2B
CMD_RAMWR = 0x2C
CMD_MADCTL = 0x36
CMD_COLMOD = 0x3A

# 16 bit per pixel (RGB565) for both the MCU and the RGB interface.
COLMOD_RGB565 = 0x55

# --- MADCTL (0x36) bits ---------------------------------------------------
MADCTL_MY = 0x80  # row address order
MADCTL_MX = 0x40  # column address order
MADCTL_MV = 0x20  # row/column exchange -- this is what makes the panel landscape
MADCTL_ML = 0x10  # vertical refresh order
MADCTL_BGR = 0x08  # panel wiring is BGR, which is what the common modules use
MADCTL_MH = 0x04  # horizontal refresh order

# The four useful orientations. ``MV`` swaps the scan axes, so the two landscape
# values give a 320x240 raster; the ``FLIP`` variants are the same view turned
# by 180 degrees. Which one reads the right way round depends on how the panel
# is mounted -- if the picture comes out mirrored or upside down, take the other
# landscape constant rather than compensating in the scene.
MADCTL_PORTRAIT_BGR = MADCTL_BGR
MADCTL_PORTRAIT_FLIP_BGR = MADCTL_MY | MADCTL_MX | MADCTL_BGR
MADCTL_LANDSCAPE_BGR = MADCTL_MV | MADCTL_BGR
MADCTL_LANDSCAPE_FLIP_BGR = MADCTL_MY | MADCTL_MX | MADCTL_MV | MADCTL_BGR

# --- Power-up delays ------------------------------------------------------
# The panel runs its own power-on reset, so leave the bus alone for a moment.
POWER_ON_CYCLES = CLOCK_HZ // 200  # 5 ms
# Datasheet 8.2.2 / 8.2.12: neither a software reset nor a sleep-out may be
# followed by another command within 120 ms.
RESET_CYCLES = CLOCK_HZ * 120 // 1000
SLEEP_OUT_CYCLES = CLOCK_HZ * 120 // 1000

DELAY_WIDTH = max(POWER_ON_CYCLES, RESET_CYCLES, SLEEP_OUT_CYCLES).bit_length()


class LCD():
    """Self-contained ILI9341 TFT controller for a 240x320 panel.

    The module talks to the display over the "8-bit 8080" parallel interface
    (IM=0000) and only ever writes; chip select is assumed to be tied low
    because the bus is not shared. Unlike the previous SystemVerilog version
    there is no CPU-facing register port and no pixel-stream handshake. The
    module brings the panel up on its own and then redraws the frame buffer
    forever, sampling every pixel from the attached
    :class:`~.objects.GraphicsStash` -- the same pixel source the VGA output
    uses.

    The panel is smaller than the 640x480 master space the scene is drawn in
    and, in ``MADCTL_LANDSCAPE_BGR``, it is also turned a quarter turn against
    it. Wrap the scene in a :class:`~.transform.Viewport` to bridge that::

        view = Viewport(engine, scene, scale=2)          # 640x480 -> 320x240
        lcd = LCD(engine, view, madctl=MADCTL_LANDSCAPE_BGR)

    The rotation itself is done by the panel: ``MADCTL_MV`` exchanges its row
    and column addressing, so the controller scans 320 columns by 240 rows and
    the frame arrives in memory order regardless. That leaves the viewport with
    a pure power-of-two scale, which is wiring. Rotating in the fabric instead
    (portrait ``madctl``, ``rotate=90`` on the viewport) gives the same picture
    at the cost of a subtractor, and is the way out if the panel is mounted so
    that no MADCTL value lines up.

    Bus timing at 25 MHz: one byte takes two clock cycles, WRn low for the
    first and high for the second. That is an 80 ns write cycle with 40 ns
    pulses, comfortably inside the ILI9341 limits of twc >= 66 ns and
    twrl/twrh >= 15 ns (the old 32 MHz implementation had to overdrive twc).

    A pixel is two bytes plus one cycle for the loop condition, so a frame
    costs ``240 * 320 * 5`` cycles -- about 15 ms, or 65 frames per second.
    The panel therefore runs free against the 60 Hz VGA output; both sample the
    same combinational scene, so only the master may drive :meth:`tick`.
    """

    def __init__(self, engine: Engine, stash: GraphicsStash | None = None, madctl: int = MADCTL_PORTRAIT_BGR):
        self.engine = engine
        self.stash = stash if stash is not None else GraphicsStash(engine)
        self.madctl = madctl

        # MADCTL decides which way the controller walks its frame memory, and
        # with it what a "line" is for the counters and the CASET/PASET windows
        # below. Everything downstream of here is in panel scan order.
        swap_axes = bool(madctl & MADCTL_MV)
        self.h_pixels = NATIVE_V_PIXELS if swap_axes else NATIVE_H_PIXELS
        self.v_pixels = NATIVE_H_PIXELS if swap_axes else NATIVE_V_PIXELS

        # A viewport knows the raster it can serve, so a scale or rotation that
        # does not fit the chosen orientation is caught here instead of showing
        # up as a torn picture on the bench.
        source_width = getattr(self.stash, 'width', None)
        source_height = getattr(self.stash, 'height', None)
        if source_width is not None and (source_width, source_height) != (self.h_pixels, self.v_pixels):
            raise ValueError(
                f'pixel source serves {source_width}x{source_height}, '
                f'but MADCTL 0x{madctl:02X} scans {self.h_pixels}x{self.v_pixels}'
            )

        # Position of the pixel currently being pushed into the frame memory.
        # ``pix_y`` needs one extra step beyond the last line, because reaching
        # ``v_pixels`` is what terminates the frame.
        self.pix_x = engine.define_local('pix_x', (self.h_pixels - 1).bit_length(), reset_value=0)
        self.pix_y = engine.define_local('pix_y', self.v_pixels.bit_length(), reset_value=0)

        self.lcd_d_out = engine.define_output('lcd_d_out', 8)
        self.lcd_wr_n = engine.define_output('lcd_wr_n', 1, reset_value=1)
        self.lcd_d_c_n = engine.define_output('lcd_d_c_n', 1, reset_value=1)
        self.lcd_vsync = engine.define_output('lcd_vsync', 1)
        # This module never reads and the data bus is always driven by us.
        self.lcd_rd_n = engine.define_output('lcd_rd_n', 1, value=Const(1))
        self.lcd_d_en = engine.define_output('lcd_d_en', 1, value=Const(1))

        self.timer = engine.create_timer(width=DELAY_WIDTH, instance_name_prefix='I_LCD_DELAY')

        # Colour of the pixel at (pix_x, pix_y). Bound to the stash in run().
        self.pixel_color = None

    def run(self):
        # Bind the pixel source to the position counters as a single continuous
        # assignment, so the (potentially deep) mux tree inside the stash is
        # built once instead of once per state that reads a colour. This has to
        # happen in run() rather than in __init__ so that every GraphicsObject
        # is already registered with the stash.
        self.pixel_color = self.engine.define_local('pixel_color', 3, value=self.stash.color(self.pix_x, self.pix_y))

        self._init_display()

        with self.engine.while_loop(Const(True)):
            self._begin_frame()

            with self.engine.while_loop(self.pix_y != self.v_pixels):
                self._write_pixel()

    # --- ILI9341 bring-up ------------------------------------------------

    def _init_display(self):
        """Bring the panel out of reset and into RGB565 mode. Runs once."""
        # The reset state already carries every reset value, so step out of it
        # before assigning anything ourselves.
        self.engine.sync()

        self.timer.wait_delay(POWER_ON_CYCLES)

        self._write_command(CMD_SWRESET)
        self.timer.wait_delay(RESET_CYCLES)

        self._write_command(CMD_SLPOUT)
        self.timer.wait_delay(SLEEP_OUT_CYCLES)

        self._write_command(CMD_COLMOD, COLMOD_RGB565)
        self._write_command(CMD_MADCTL, self.madctl)
        self._write_command(CMD_DISPON)

    def _begin_frame(self):
        """Open the full frame memory for writing and rewind the counters.

        ``lcd_vsync`` is held high for the duration of this setup, so the rest
        of the design can use it as a frame-start marker.
        """
        self.engine.set(self.lcd_vsync, 1)

        self._write_command(CMD_CASET, 0, 0, (self.h_pixels - 1) >> 8, (self.h_pixels - 1) & 0xFF)
        self._write_command(CMD_PASET, 0, 0, (self.v_pixels - 1) >> 8, (self.v_pixels - 1) & 0xFF)
        self._write_command(CMD_RAMWR)

        self.engine.set(self.lcd_vsync, 0)
        self.engine.set(self.pix_x, 0)
        self.engine.set(self.pix_y, 0)
        # Leave the counter reset behind before the pixel loop starts, so that
        # looping back to the loop head does not rewind the frame again.
        self.engine.sync()

    # --- Pixel output ----------------------------------------------------

    def _write_pixel(self):
        """Push one RGB565 pixel into the frame memory. Costs four cycles."""
        self._write_byte(self._rgb565_high())
        self.engine.sync()
        self._write_byte(self._rgb565_low())

        # Advance during the trailing WRn-high cycle, which is idle anyway.
        # Both bytes above have already been latched from the old position, so
        # they still belong to the pixel we just finished.
        last_column = self.pix_x == (self.h_pixels - 1)
        self.engine.set(self.pix_x, IfThenElse(last_column, 0, self.pix_x + 1))
        self.engine.set(self.pix_y, IfThenElse(last_column, self.pix_y + 1, self.pix_y))

    def _rgb565_high(self):
        """Upper RGB565 byte: five red bits and the top three green bits."""
        return Concat(*[self.red] * 5, *[self.green] * 3)

    def _rgb565_low(self):
        """Lower RGB565 byte: the bottom three green bits and five blue bits."""
        return Concat(*[self.green] * 3, *[self.blue] * 5)

    # The stash reports one bit per channel, the same encoding the VGA output
    # drives onto its three 1-bit channels. Replicating each bit across its
    # whole RGB565 field maps a set channel to full intensity.
    @property
    def red(self):
        return self.pixel_color[2]

    @property
    def green(self):
        return self.pixel_color[1]

    @property
    def blue(self):
        return self.pixel_color[0]

    # --- 8080 bus primitives ---------------------------------------------

    def _write_byte(self, data, is_command: bool = False):
        """Drive one byte onto the bus, WRn low for a cycle and then high.

        Returns with the engine still inside the WRn-high cycle, so a caller
        can attach further assignments to it instead of spending a state of its
        own. Chain further bytes with an explicit ``sync()``.
        """
        self.engine.set(self.lcd_d_out, data)
        self.engine.set(self.lcd_d_c_n, 0 if is_command else 1)
        self.engine.set(self.lcd_wr_n, 0)
        self.engine.sync()
        self.engine.set(self.lcd_wr_n, 1)

    def _write_command(self, command: int, *data: int):
        """Send a command byte followed by its data bytes, then idle one cycle."""
        self._write_byte(command, is_command=True)
        for byte in data:
            self.engine.sync()
            self._write_byte(byte)
        self.engine.sync()
