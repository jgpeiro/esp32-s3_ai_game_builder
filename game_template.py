import uasyncio as asyncio
import machine
import framebuf
import st7789
import time
import neopixel
import logging

machine.freq(int(240e6))

DT_ms = 100  # Frame delay in seconds for asyncio

# Pin setup
button_a = machine.Pin(40, machine.Pin.IN, machine.Pin.PULL_UP)
button_b = machine.Pin(41, machine.Pin.IN, machine.Pin.PULL_UP)
button_c = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)
button_d = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)
joystick_up = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
joystick_down = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_UP)
joystick_left = machine.Pin(42, machine.Pin.IN, machine.Pin.PULL_UP)
joystick_right = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)

# LCD setup
LCD_WIDTH = 240
LCD_HEIGHT = 240
SPI_BAUDRATE = 80_000_000

sck = machine.Pin(35, machine.Pin.OUT, value=0)
mosi= machine.Pin(36, machine.Pin.OUT, value=0)
spi = machine.SPI(1, baudrate=SPI_BAUDRATE ) # This line is required due to a bug in the SPI code.
spi = machine.SPI(1, baudrate=SPI_BAUDRATE, polarity=0, phase=0, sck=sck, mosi=mosi, miso=None)

rst= machine.Pin(37, machine.Pin.OUT, value=0)
cs = machine.Pin(34, machine.Pin.OUT, value=1)
dc = machine.Pin(33, machine.Pin.OUT, value=0)
bl = machine.Pin(38, machine.Pin.OUT, value=0)

#class ST7789:
#    def __init__( self, spi, rst, cs, dc, bl, width, height ):
lcd = st7789.ST7789(spi, rst, cs, dc, bl, LCD_WIDTH, LCD_HEIGHT)
fb_buf = bytearray(LCD_WIDTH * LCD_HEIGHT * 2)
fb = framebuf.FrameBuffer(fb_buf, LCD_WIDTH, LCD_HEIGHT, framebuf.RGB565)

# PWM setup
speaker_pin = machine.Pin(11)
speaker = machine.PWM(speaker_pin, freq=1000, duty_u16=0)
speaker.deinit() # This line is required due to a bug in the PWM code.
speaker = machine.PWM(speaker_pin, freq=1000, duty_u16=0)

# RGB led
rgb_led_pin = machine.Pin( 21, machine.Pin.OUT )
rgb_led = neopixel.NeoPixel(rgb_led_pin, 1)
rgb_led[0] = (0,0,0)
rgb_led.write()

# Framebuffer API
#class FrameBuffer:
#    def fill(self, c: int) -> None:
#    def pixel(self, x: int, y: int, [c: int = None]) -> [int]:
#    def hline(self, x: int, y: int, w: int, c: int) -> None:
#    def vline(self, x: int, y: int, h: int, c: int) -> None:
#    def line(self, x1: int, y1: int, x2: int, y2: int, c: int) -> None:
#    def rect(self, x: int, y: int, w: int, h: int, c: int [, f: bool = False]) -> None:
#    def ellipse(self, x: int, y: int, xr: int, yr: int, c: int [, f: bool = False] [, m: int = None]) -> None:
#    def poly(self, x: int, y: int, coords: List[int], c: int [, f: bool = False]) -> None:
#    def text(self, s: str, x: int, y: int [, c: int = 1]) -> None:
#    def scroll(self, xstep: int, ystep: int) -> None:
#    def blit(self, fbuf: 'FrameBuffer', x: int, y: int, key: int = -1 [, palette: 'FrameBuffer' = None]) -> None:
# Note 1: There is no circle function, use ellipse instead.
# Note 2: The poly requires coords as array.array( "h", [...] )

class colors:
    BLACK = const(0x0000)
    WHITE = const(0xFFFF)
    RED = const(0x00F8)
    GREEN = const(0xE007)
    BLUE = const(0x1F00)
    CYAN = const(0xFF07)
    MAGENTA = const(0x1FF8)
    YELLOW = const(0xE0FF)
    ORANGE = const(0x20FD)
    INDIGO = const(0x1048)
    VIOLET = const(0x1080)

    @staticmethod
    def color_brightness(color, brightness):
        if brightness < 0 or brightness > 1:
            return color
        r = (color >> 11) & 0x1F
        g = (color >> 5) & 0x3F
        b = color & 0x1F
        r = int(r * brightness)
        g = int(g * brightness)
        b = int(b * brightness)
        return (r << 11) | (g << 5) | b

class Queue:
    def __init__(self):
        self.items = []

    def put(self, item):
        self.items.append(item)

    async def get(self):
        while not self.items:
            await asyncio.sleep(0)
        return self.items.pop(0)

class SoundEngine:
    def __init__(self):
        self.queue = Queue()

    async def run(self):
        while True:
            sound_event = await self.queue.get()
            await self.play_sound(sound_event)

    async def play_sound(self, sound_event):
        logging.info( f"play_sound({sound_event})" )
        if sound_event == "game_start":
            await play_game_start_sound()
        elif sound_event == "button_press":
            await play_button_press_sound()

# Sound functions
async def play_tone(frequency, duration):
    speaker.freq(frequency)
    speaker.duty_u16(30000)  # Set a duty cycle for the tone
    await asyncio.sleep(duration)
    speaker.duty_u16(0)  # Turn off the sound

async def play_game_start_sound():
    await play_tone(440, 0.2)  # A4
    await play_tone(880, 0.2)  # A5
    await play_tone(660, 0.2)  # E5

async def play_button_press_sound():
    await play_tone(880, 0.1)  # A5

# Drawing functions
def draw_gradient(fb, start_color, end_color):
    for y in range(LCD_HEIGHT):
        ratio = y / LCD_HEIGHT
        r = int(((end_color >> 11) & 0x1F) * ratio + ((start_color >> 11) & 0x1F) * (1 - ratio))
        g = int(((end_color >> 5) & 0x3F) * ratio + ((start_color >> 5) & 0x3F) * (1 - ratio))
        b = int((end_color & 0x1F) * ratio + (start_color & 0x1F) * (1 - ratio))
        color = (r << 11) | (g << 5) | b
        color2 = color
        color = ((color2&0x00FF) << 8) | ((color2&0xFF00) >> 8)
        fb.hline(0, y, LCD_WIDTH, color)

def create_player_sprite(color):
    sprite_size = 8
    buf = bytearray(sprite_size * sprite_size * 2)
    fb_sprite = framebuf.FrameBuffer(buf, sprite_size, sprite_size, framebuf.RGB565)
    fb_sprite.fill(color)
    fb_sprite.fill_rect(2, 2, 4, 4, colors.WHITE)  # Example of adding details to the sprite
    return fb_sprite, buf

def draw_sprite(fb, sprite_fb, sprite_buf, x, y):
    fb.blit(sprite_fb, x, y)

# Game class
class Game:
    def __init__(self, sound_engine):
        self.player_x = LCD_WIDTH // 2
        self.player_y = LCD_HEIGHT // 2
        self.player_sprite, self.player_buf = create_player_sprite(colors.RED)
        self.sound_engine = sound_engine
        self.events_bck = [False, False, False, False, False, False, False, False]

    def is_running(self):
        return True  # Implement actual logic to check if the game is running

    async def update(self, events):
        if events[0]:  # Up
            self.player_y -= 1
        if events[1]:  # Down
            self.player_y += 1
        if events[2]:  # Left
            self.player_x -= 1
        if events[3]:  # Right
            self.player_x += 1
        if events[4]:  # A
            self.sound_engine.queue.put("button_press")  # Queue sound event
        
        if events[0] and not self.events_bck[0]:
            logging.info( "Game.update pressed up" )
        elif not events[0] and self.events_bck[0]:
            logging.info( "Game.update released up" )
        
        if events[1] and not self.events_bck[1]:
            logging.info( "Game.update pressed down" )
        elif not events[1] and self.events_bck[1]:
            logging.info( "Game.update released down" )

        if events[2] and not self.events_bck[2]:
            logging.info( "Game.update pressed left" )
        elif not events[2] and self.events_bck[2]:
            logging.info( "Game.update released left" )

        if events[3] and not self.events_bck[3]:
            logging.info( "Game.update pressed right" )
        elif not events[3] and self.events_bck[3]:
            logging.info( "Game.update released right" )

        if events[4] and not self.events_bck[4]:
            logging.info( "Game.update pressed A" )
        elif not events[4] and self.events_bck[4]:
            logging.info( "Game.update released A" )

        self.events_bck = events

    async def draw(self, fb):
        fb.fill(colors.BLACK)  # Clear the screen
        draw_gradient(fb, colors.BLUE, colors.CYAN)  # Draw the background gradient
        draw_sprite(fb, self.player_sprite, self.player_buf, self.player_x, self.player_y)


# Main game loop
async def main_loop(game):
    game.sound_engine.queue.put("game_start")  # Queue game start sound
    while game.is_running():
        events = [
            not joystick_up.value(),
            not joystick_down.value(),
            not joystick_left.value(),
            not joystick_right.value(),
            not button_a.value(),
            not button_b.value(),
            not button_c.value(),
            not button_d.value()
        ]
        
        t0 = time.ticks_ms()
        await game.update( events )
        await game.draw(fb)
        lcd.write_bmp(fb_buf)
        t1 = time.ticks_ms()

        dt = t1 - t0  # Convert to seconds
        if dt < DT_ms:
            await asyncio.sleep_ms(DT_ms - dt)
        else:
            logging.warning( f"{dt} < DT_ms" )
            await asyncio.sleep_ms(0)
    
    asyncio.new_event_loop() # game over should always start a new loop

# Run the game
async def run_game():
    sound_engine = SoundEngine()
    game = Game(sound_engine)
    
    # Start the sound engine task
    sound_task = asyncio.create_task(sound_engine.run())
    game_task = asyncio.create_task(main_loop(game))
    
    await asyncio.gather(sound_task, game_task)


logging.basicConfig(level=logging.INFO)
# Start the game loop
asyncio.run(run_game())
