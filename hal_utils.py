import machine
import st7789
import neopixel

SPI_BAUDRATE = 80_000_000
LCD_WIDTH, LCD_HEIGHT = 240, 240
CPU_FREQ = int( 240e6 )

# HAL initialization
btn_a, btn_b, btn_c, btn_d = None, None, None, None
joy_up, joy_down, joy_left, joy_right, joy_center = None, None, None, None, None
spi = None
lcd = None

def init():
    global btn_a, btn_b, btn_c, btn_d
    global joy_up, joy_down, joy_left, joy_right, joy_center
    global spi
    global lcd
    
    machine.freq( CPU_FREQ )
    
    # Buttons
    btn_a = machine.Pin(40, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_b = machine.Pin(41, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_c = machine.Pin( 2, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_d = machine.Pin( 5, machine.Pin.IN, machine.Pin.PULL_UP)
    joy_up     = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
    joy_down   = machine.Pin( 1, machine.Pin.IN, machine.Pin.PULL_UP)
    joy_left   = machine.Pin(42, machine.Pin.IN, machine.Pin.PULL_UP)
    joy_right  = machine.Pin( 4, machine.Pin.IN, machine.Pin.PULL_UP)
    joy_center = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)

    # SPI
    
    sck = machine.Pin(35, machine.Pin.OUT, value=0)
    mosi= machine.Pin(36, machine.Pin.OUT, value=0)
    spi = machine.SPI(2, baudrate=SPI_BAUDRATE )
    spi = machine.SPI(2, baudrate=SPI_BAUDRATE, polarity=0, phase=0, sck=sck, mosi=mosi, miso=None)

    # LCD
    
    rst= machine.Pin(37, machine.Pin.OUT, value=0)
    cs = machine.Pin(34, machine.Pin.OUT, value=1)
    dc = machine.Pin(33, machine.Pin.OUT, value=0)
    bl = machine.Pin(38, machine.Pin.OUT, value=0)
    lcd = st7789.ST7789(spi, rst, cs, dc, bl, LCD_WIDTH, LCD_HEIGHT)

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
