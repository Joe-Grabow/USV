"""
Created on 01.01.2024 0:00:00

Program history
01.01.2024    V. 00.50    init Version CRC8 modul (Author Franke)

CRC8 Modul with
cCRC8 Class
- calculate the CRC8 check sum for a byte stream over a internal saved table
- use the internal micropython.const function
- TODO Initialization value
- TODO final XOR
- TODO reflect input and output

@author: S. Franke
"""

__version__ = '00.50'
__author__ = 'S. Franke'


class cCRC8:
    def __init__(self, generator:bytes):
        '''
        cCRC8 Class
          - calculate a checksum from a byte stream with an user generator polynom
          
        cCRC8(generator:bytes)
        - input values
          generator - genator polynom for the CRC8 calculation : bytes(1)
        '''
        self.crctable = None
        self.CRCSum = 0
        self.generator = __import__("micropython").const(generator)
        self.__CalculateTable__()
        return
    
    def __CalculateTable__(self):
        '''
        internal function to calculate the table
        __CalculateTable__()
        - input values
          None
        '''
        self.crctable = bytearray(256)
        iGenerator = int.from_bytes(self.generator, "little")
        for dividend in range(0,256):
            currByte = dividend
            for bit in range(0,8):
                if (currByte & 0x80) != 0:
                    currByte = currByte << 1
                    currByte = currByte ^ iGenerator
                else:
                    currByte = currByte << 1
            self.crctable[dividend] = currByte & 0xFF
        return
    
    def calc(self, data:bytearray):
        '''
        calc function to calculate the CRC sum from one bytearray
        calc(data:bytearray)
        - input values
          data - data bytearray
        - return value
          - CRC8 sum from data bytearray
        '''
        self.CRCSum = 0
        self.update(data)
        return self.CRCSum
    
    def start(self, data:bytearray):
        '''
        picewise calc function to calculate the CRC sum from more as one bytearrays
         - start function for the first bytes
        start(data:bytearray)
        - input values
          data - data bytearray
        - return value
          None
        '''
        self.CRCSum = 0
        self.update(data)
        return
    
    def update(self, data:bytearray):
        '''
        picewise calc function to calculate the CRC sum from more as one bytearrays
         - update function for the middle bytes
        start(data:bytearray)
        - input values
          data - data bytearray
        - return value
          None
        '''
        for dat in data:
            dat = dat ^ self.CRCSum
            self.CRCSum = self.crctable[dat]
        return
    
    def final(self, data:bytearray):
        '''
        picewise calc function to calculate the CRC sum from more as one bytearrays
         - final function for the last bytes
        start(data:bytearray)
        - input values
          data - data bytearray
        - return value
            CRC8 sum from all data bytearrays
        '''
        self.update(data)
        return self.CRCSum

if __name__ == '__main__':
    def Test():
        CRC = cCRC8(b'\xD5')
        print(CRC.calc(b'\x87\x88\x89\x8A\x8B'))
        return CRC
    CRC = Test()
    