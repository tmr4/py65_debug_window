import sys
import time
import threading

from utils import console

class VIA():

    SR = 4
    SET_CLEAR = 128

    def __init__(self, start_addr, mpu):
        self.mpu = mpu
        self.VIA_SR  = start_addr + 0x0a   # shift register
        self.VIA_IFR = start_addr + 0x0d   # interrupt flags register
        self.VIA_IER = start_addr + 0x0e   # interrupt enable register
        self.SRThread = False
        self.escape = False
        self.quit = False
        self.dbFlag = False

        self.name = 'VIA'

        # init
        self.reset()

        self.install_interrupts()

    def check_debug(self, flag=None):
        if flag != None:
            self.dbFlag = flag
        return self.dbFlag

    def install_interrupts(self):
        def getc(address):
            char = console.getch_noblock(sys.stdin)
            if char:
                byte = ord(char)
                if self.escape:
                    self.escape = False
                    if byte == 0x51 or byte == 0x71: # handles <ESC>Q or <ESC>q
                        byte = 0
                        self.quit = True
                    elif byte == 0x44 or byte == 0x64: # handles <ESC>D or <ESC>d
                        byte = 0
                        self.dbFlag = True
                else:
                    if byte == 0x1b:
                        self.escape = True
                        byte = 0
                    else:
                        self.mpu.memory[self.VIA_IFR] &= 0xfb
            else:
                byte = 0
            return byte

        def SR_enable(address, value):
            if value & self.SET_CLEAR:
                # enable interrupts
                if value & self.SR and not self.SRThread:
                    t = threading.Thread(target=SR_thread, daemon = True)
                    self.SRThread = True
                    t.start()
            else:
                # disable interrupts
                if value & self.SR and self.SRThread:
                    self.SRThread = False

        def SR_thread():
            while(self.SRThread):
                time.sleep(.05) # delay needed to allow processing of interrupt prior to setting it again *** TODO: would be nice to eliminate this with a flag or something ***
                if (self.mpu.p & self.mpu.INTERRUPT == 0) and self.mpu.IRQ_pin:
                    if console.kbhit():
                        self.mpu.memory[self.VIA_IFR] |= 0x04
                        self.mpu.IRQ_pin = 0
                        count_irq = 0   # we need a short delay here
                        while count_irq < 100:
                            count_irq += 1

        self.mpu.memory.subscribe_to_write([self.VIA_IER], SR_enable)
        self.mpu.memory.subscribe_to_read([self.VIA_SR], getc)

    def reset(self):
        self.mpu.memory[self.VIA_IER] = 0
        self.mpu.memory[self.VIA_IFR] = 0

    #def irq(self):
        #return (IFR6 and IER6) or (IFR5 and IER5) or (IFR4 and IER4) or (IFR3 and IER3) or (IFR2 and IER2) or (IFR1 and IER1) or (IFR0 and IER0)
        #return (self.mpu.memory[self.VIA_IFR] and self.SR) and ((self.mpu.memory[self.VIA_IER] and self.SR))

