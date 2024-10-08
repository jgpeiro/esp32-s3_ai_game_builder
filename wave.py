import struct

class Wave:
    HEADER_FMT = "<4sI4s4sIHHIIHH4sI"
    FORMAT_PCM = 1
    
    def __init__(self, fl, freq=8000, bits=16, channels=1):
        self.freq = freq
        self.bits = bits
        self.channels = channels
        self.size = 0
        self.fl = fl
        self.fl.write( self.build_header() )
        
    def build_header(self):
        header = struct.pack(self.HEADER_FMT,
            b'RIFF',
            self.size + struct.calcsize(self.HEADER_FMT) - 8,
            b'WAVE',
            b'fmt ',
            16,  # Size of fmt chunk
            self.FORMAT_PCM,
            self.channels,
            self.freq, 
            (self.freq*self.channels*self.bits)//8,
            (self.channels*self.bits)//8,
            self.bits,
            b'data',
            self.size
        )
        return header
    
    def write(self, buf):
        self.size += self.fl.write( buf )
    
    def close(self):
        self.fl.seek(0)
        self.fl.write( self.build_header() )
#         self.fl.close()

