import time
import machine
import framebuf

class ST7789:
    def __init__( self, spi, rst, cs, dc, bl, width, height ):
        self.rst = rst
        self.cs = cs
        self.spi = spi
        self.dc = dc
        self.bl = bl
        self.width = width
        self.height = height
        self.buf = bytearray(1)
        self.buf4 = bytearray(4)
        self.reset()
        self.config()
        self.bl.value(1)
    
    def reset( self ):
        self.rst.value(0)
        self.cs.value(1)
        self.dc.value(0)
        time.sleep_ms(1)
        self.rst.value(1)
        time.sleep_ms(10)
   
    def write_cmd(self, cmd, data=b"" ):
        self.buf[0] = cmd
        self.cs.value(0)
        self.spi.write( self.buf )
        if( len(data) > 0 ):
            self.dc.value(1)
            self.spi.write( data )
            self.dc.value(0)
        self.cs.value(1)

    def config(self):
        self.write_cmd(0x36, b"\x70")
        self.write_cmd(0x3A, b"\x05")
        self.write_cmd(0xB2, b"\x0C\x0C\x00\x33\x33")
        self.write_cmd(0xB7, b"\x35")
        self.write_cmd(0xBB, b"\x19")
        self.write_cmd(0xC0, b"\x2C")
        self.write_cmd(0xC2, b"\x01")
        self.write_cmd(0xC3, b"\x12")
        self.write_cmd(0xC4, b"\x20")
        self.write_cmd(0xC6, b"\x0F")
        self.write_cmd(0xD0, b"\xA4\xA1")
        self.write_cmd(0xE0, b"\xD0\x04\x0D\x11\x13\x2B\x3F\x54\x4C\x18\x0D\x0B\x1F\x23")
        self.write_cmd(0xE1, b"\xD0\x04\x0C\x11\x13\x2C\x3F\x44\x51\x2F\x1F\x1F\x20\x23")
        self.write_cmd(0x21)
        self.write_cmd(0x11)
        self.write_cmd(0x29)
    
    def write_bmp(self, buf, x=0, y=0, width=None, height=None ):
        if( not width ):
            width = self.width
        if( not height ):
            height = self.height
        
        self.buf4[0] = x >> 8
        self.buf4[1] = x >> 0
        self.buf4[2] = (x+width-1) >> 8
        self.buf4[3] = (x+width-1) >> 0
        self.write_cmd(0x2A, self.buf4 )

        self.buf4[0] = y >> 8
        self.buf4[1] = y >> 0
        self.buf4[2] = (y+height-1) >> 8
        self.buf4[3] = (y+height-1) >> 0
        self.write_cmd(0x2B, self.buf4 )

        self.write_cmd(0x2C, buf )

def test():
    LCD_WIDTH = 240
    LCD_HEIGHT = 240
    SPI_BAUDRATE = 80_000_000

    sck = machine.Pin( 35, machine.Pin.OUT, value=0 )
    mosi= machine.Pin( 36, machine.Pin.OUT, value=0 )
    spi = machine.SPI( 1, baudrate=SPI_BAUDRATE )
    spi = machine.SPI( 1, baudrate=SPI_BAUDRATE, polarity=0, phase=0, sck=sck, mosi=mosi, miso=None )
           
    rst = machine.Pin( 37, machine.Pin.OUT, value=0 )
    cs  = machine.Pin( 34, machine.Pin.OUT, value=1 )
    dc  = machine.Pin( 33, machine.Pin.OUT, value=0 )
    bl  = machine.Pin( 38, machine.Pin.OUT, value=0 )

    lcd = ST7789( spi, rst, cs, dc, bl, LCD_WIDTH, LCD_HEIGHT )

    buffer = bytearray( LCD_WIDTH*LCD_HEIGHT * 2 )
    fb = framebuf.FrameBuffer(buffer, LCD_WIDTH, LCD_HEIGHT, framebuf.RGB565 )

    fb.fill( 0x0000 )
    fb.text( "Hello World!", 10, 10, 0xffff )
    lcd.write_bmp( buffer )

    print("done")
