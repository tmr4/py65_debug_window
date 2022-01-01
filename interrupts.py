from devices.via65c22 import VIA
from devices.acia65c51 import ACIA

class Interrupts:
    def __init__(self, mon, mpu):
        mpu.IRQ_pin = 1
        self.via = VIA(0x8800, mpu)
        ACIA(0x8400, mpu, mon)
        
