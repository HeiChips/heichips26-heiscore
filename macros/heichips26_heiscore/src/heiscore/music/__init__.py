from nortl import Const, Engine, IfThenElse, Volatile
from nortl.components import ElasticChannel
from nortl.core.protocols import Renderable, SignalProto


class MusicSequencer:
    def __init__(self, engine: Engine, n_channels=3) -> None:
        self.engine = engine
        self.n_channels = n_channels
        self.base_tick = 3000000

        self.input_channels = [ElasticChannel(engine, 8, f'music_channel_{i}', 8) for i in range(n_channels)]
        self.channel_values = [self.engine.define_scratch(8) for _ in range(n_channels)]

        self.output_value = Volatile(self.engine.define_scratch(8), 'identical_rw')

        self.sine = [127, 227, 251, 183, 72, 4, 28, 127]

        fclk = 25e6

        freq_table_hz = [
            100,
            262,  # c1
            277,  # c#
            294,  # d
            311,
            330,
            349,
            370,
            392,
            415,
            440,
            466,
            494,
            523,
            554,
            587,
        ]

        self.tone_to_id = {
            'C': Const(1, 4),
            'C#': Const(2, 4),
            'D': Const(3, 4),
            'D#': Const(4, 4),
            'E': Const(5, 4),
            'F': Const(6, 4),
            'F#': Const(7, 4),
            'G': Const(8, 4),
            'G#': Const(9, 4),
            'A': Const(10, 4),
            'A#': Const(11, 4),
            'H': Const(12, 4),
            'C2': Const(13, 4),
            'C2#': Const(14, 4),
            'D2': Const(15, 4),
        }

        self.delay_for_tone = [int(fclk // 8 // ftone) for ftone in freq_table_hz]

    def sine_lookup(self, pos: Renderable) -> Renderable:
        ret = 127

        clipped_pos = pos & 7

        for i, item in enumerate(self.sine):
            ret = IfThenElse(clipped_pos == i, self.sine[i], ret)

        return ret

    def tone_lookup(self, pos: Renderable) -> Renderable:
        ret = Const(0, 16)

        for i, item in enumerate(self.delay_for_tone):
            ret = IfThenElse(pos == i, self.delay_for_tone[i], ret)

        return ret

    def build_channels(self):

        for i in range(self.n_channels):
            channel_delay_timer = self.engine.create_timer(24)
            current_tone = Volatile(self.engine.define_scratch(4), 'identical_rw')

            with self.engine.fork(f'music_channel_tone_control{i}'):  # noqa: SIM117
                with self.engine.while_loop(Const(True)):
                    data = self.input_channels[i].receive()
                    tone = data & 0xF
                    duration = data >> 4

                    with self.engine.for_loop(0, duration):
                        channel_delay_timer.wait_delay(self.base_tick)
                        self.engine.set(current_tone, tone)

            current_idx = self.engine.define_scratch(3)
            sine_step_timer = self.engine.create_timer(16)

            with self.engine.fork(f'music_channel_tone_to_sine{i}'):  # noqa: SIM117
                with self.engine.while_loop(Const(True)):
                    self.engine.set(self.channel_values[i], IfThenElse(current_tone != 0, self.sine_lookup(current_idx), 127))
                    self.engine.set(current_idx, current_idx + 1)
                    self.engine.sync()
                    sine_step_timer.wait_delay(self.tone_lookup(current_tone))

        # Assemble output value

        with self.engine.fork('music_assembler'):  # noqa: SIM117
            with self.engine.while_loop(Const(True)):
                s = Const(0, 8)
                for i in range(self.n_channels):
                    s += Volatile(self.channel_values[i], 'identical_rw') / self.n_channels

                self.engine.set(self.output_value, s)


class MusicSequencerPWM(MusicSequencer):
    def __init__(self, engine: Engine, output_pwm: SignalProto, n_channels=3) -> None:
        super().__init__(engine, n_channels)

        self.pwm = output_pwm

        self.pwm_timer = self.engine.create_timer()

        data_latch = self.engine.define_scratch(9)

        with self.engine.fork('Music_generator_PWM'):  # noqa:SIM117
            with self.engine.while_loop(Const(True)):
                self.engine.set(data_latch, self.output_value)
                self.engine.set(self.pwm, 1)
                self.pwm_timer.wait_delay(data_latch)
                self.engine.set(self.pwm, 0)
                self.pwm_timer.wait_delay(255 - data_latch)
