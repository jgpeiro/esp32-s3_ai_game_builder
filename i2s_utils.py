import time
import io
import machine
import wave
import asyncio
import api_utils

async def _play( key, text, cb_complete=None ):
    PIN_SCK = 15
    PIN_WS = 16
    PIN_SD = 12

    I2S_ID = 0
    I2S_BITS = 16
    I2S_CH = 1
    I2S_RATE = 24000
    I2S_LEN = 1024 * 8

    i2s = machine.I2S(
        I2S_ID,
        sck=machine.Pin(PIN_SCK),
        ws=machine.Pin(PIN_WS),
        sd=machine.Pin(PIN_SD),
        mode=machine.I2S.TX,
        bits=I2S_BITS,
        format=machine.I2S.MONO,
        rate=I2S_RATE,
        ibuf=I2S_LEN,
    )

    writer = asyncio.StreamWriter(i2s, {})
    
    async def acallback( response ):
        await response.read(44) # skip wav header
        buf = await response.read(1024)
        while( buf ):
            await writer.awrite(buf)
            buf = await response.read(1024)
            if( cb_complete ):
                if( cb_complete() ):
                    break
    
    for line in text.split( "\n" ):
        for sentence in line.split( "." ):
            for part in sentence.split( "," ):
                if( len(part) > 4 ):
                    await api_utils.text_to_speech( key, part, acallback )
                    if( cb_complete ):
                        if( cb_complete() ):
                            i2s.deinit()
                            return
       
    i2s.deinit()

class asyncio_Queue:
    def __init__(self):
        self.items = []

    async def put(self, item):
        self.items.append(item)

    async def get(self):
        while not self.items:
            await asyncio.sleep(0)
        return self.items.pop(0)

async def play(key, text, cb_complete=None):
    PIN_SCK = 15
    PIN_WS = 16
    PIN_SD = 12
    I2S_ID = 0
    I2S_BITS = 16
    I2S_CH = 1
    I2S_RATE = 24000
    I2S_LEN = 1024 * 8
    i2s = machine.I2S(
        I2S_ID,
        sck=machine.Pin(PIN_SCK),
        ws=machine.Pin(PIN_WS),
        sd=machine.Pin(PIN_SD),
        mode=machine.I2S.TX,
        bits=I2S_BITS,
        format=machine.I2S.MONO,
        rate=I2S_RATE,
        ibuf=I2S_LEN,
    )
    writer = asyncio.StreamWriter(i2s, {})
    
    queue = asyncio_Queue()
    
    async def reader_task(response):
        await response.read(44)  # skip wav header
        while True:
            buf = await response.read(1024)
            if not buf:
                await queue.put(None)  # Signal end of stream
                break
            await queue.put(buf)
    
    async def writer_task():
        while True:
            buf = await queue.get()
            if buf is None:
                break
            await writer.awrite(buf)
            if cb_complete and cb_complete():
                break
    
    async def acallback(response):
        reader = asyncio.create_task(reader_task(response))
        writer = asyncio.create_task(writer_task())
        await asyncio.gather(reader, writer)
    
    async def process_text():
        for line in text.split("\n"):
            for sentence in line.split("."):
                for part in sentence.split(","):
                    if len(part) > 4:
                        await api_utils.text_to_speech(key, part, acallback)
                        if cb_complete and cb_complete():
                            return
    
    try:
        await process_text()
    finally:
        i2s.deinit()

async def record( cb_complete=None, timeout=5 ):
    PIN_SCK = 15
    PIN_WS = 16
    PIN_SD = 17

    I2S_ID = 0
    I2S_BITS = 16
    I2S_CH = 1
    I2S_RATE = 8000
    I2S_LEN = 1024 * 4

    i2s = machine.I2S(
        I2S_ID,
        sck=machine.Pin(PIN_SCK),
        ws=machine.Pin(PIN_WS),
        sd=machine.Pin(PIN_SD),
        mode=machine.I2S.RX,
        bits=I2S_BITS,
        format=machine.I2S.MONO,
        rate=I2S_RATE,
        ibuf=I2S_LEN * 4,
    )

    fl_wav = io.BytesIO()
    wav = wave.Wave(fl_wav, freq=I2S_RATE, bits=I2S_BITS, channels=I2S_CH)

    sreader = asyncio.StreamReader(i2s)
    i2s_buf = bytearray(1024)
    i2s_mv = memoryview(i2s_buf)
    
    min_timeout = 1
    t0 = time.time()
    while( time.time() - t0 < timeout ):
        num_bytes_read = await sreader.readinto(i2s_mv)
        if num_bytes_read > 0:
            wav.write(i2s_mv[:num_bytes_read])
        await asyncio.sleep_ms(10)  # Yield control to the event loop
        if( cb_complete ):
            if( not cb_complete() ):
                if( time.time() - t0 > min_timeout ):
                    break
    
    wav.close()
    i2s.deinit()
    return fl_wav