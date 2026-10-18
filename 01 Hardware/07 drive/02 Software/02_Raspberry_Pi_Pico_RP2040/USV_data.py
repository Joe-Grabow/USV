"""
USV Data Communication Module

Created on 2026-03-26

Program history:
26.03.2026    V. 01.00    Initiale Version (Author: C. Händel)

Description:
- Implementiert die Kommunikation mit einem USV-Slave über UART
- Vor der Initialisierung eines Objekts der Klasse ist zuerst USV_data.setup(slave_ID, uart) aufzurufen
- Hardware-UART zwingend mit timeout und timeout_char sowie folgender Konfiguration:
  (baudrate=250000, bits=8, parity=1, stop=1)
- Objekte ermöglichen dann Instanzen für jede value_ID
- Unterstützt Lesen und Schreiben von Daten über definierte Frames
- Nutzt CRC8 zur Datenvalidierung

TODO:
- UART TX und RX perspektivisch über PIO-UART mit Paritätsprüfung und Timeout ermöglichen.

@author: C. Händel
"""

__version__ = '01.00'
__author__ = 'C. Händel'

# --- Imports ---
from micropython import const
import json
from CRC8 import cCRC8

# --- Klasse: USV_data ---
class USV_data:
    """
    Klasse zur Kommunikation mit einem USV-Slave.

    Funktionen:
    - Senden von Request-Frames
    - Empfangen und Prüfen von Response-Frames
    - Schreiben von Daten inkl. CRC8
    """

    # --- Frame-Konstanten ---
    __STARTBYTE = const(0xA5)
    __ENDBYTE = const(0xA6)
    __FRAME_LEN_READ = const(8)
    
    # --- Klassenvariablen ---
    _slave_ID = None   # feste Slave-ID
    _uart = None       # fester UART
    _datablock = None  # Inhalt der JSON-Datei

    # --- Klassenmethoden ---
    @classmethod
    def setup(cls, slave_ID, uart):
        """
        Kommunikationeinstellungen mit dem USV-Slave
        - Prüft und setzt die feste Slave_ID und den UART
        - Prüft, ob die json-Datei bereits einmal eingelesen wurde.
        - Prüft und öffnet die json-Datei (nur einmal laden, falls für jede value_ID ein Objekt erzeugt wird)

        param: slave_ID (Byte): Slave-Adresse (0–255)
        param: uart (UART): Hardware mit definierten Timeouts
        return: None
        """
        
        # --- Slave-ID prüfen ---
        if isinstance(slave_ID, int) and slave_ID <= 255 and slave_ID >= 0:
            cls._slave_ID = slave_ID
        else:
            raise ValueError('slave_ID is not a byte from 0 to 255')
        
        # --- UART prüfen ---
        if type(uart).__name__ == 'UART': 
            cls._uart = uart
        else:
            raise ValueError('uart is not type UART')
        
        # --- JSON-Daten laden ---
        if cls._datablock is None: # Klassenvariable, um json-Datablock nur einmal zu laden, falls mehrere Objekte erzeugt werden.
            try:
                with open('./datablock.json') as file:
                    cls._datablock = json.load(file)
            except OSError:
                raise RuntimeError("Cannot open './datablock.json'")
            except ValueError:
                raise RuntimeError("Invalid JSON in './datablock.json'")    

    
    # --- Init ---
    def __init__(self, value_ID):
        """
        - Initialisiert das USV-Objekt.
        - Prüft, ob setup() bereits einmal aufgerufen wurde.
        - Je nach Performanceanforderung kann für jede value_ID ein Objekt erzeugt
          oder diese in einem Objekt geändert werden. (Vorschlag: Für jede value_ID ein Objekt)

        param: value_ID (String): ID des Datenwerts
        
        return: None
        """
        
        if type(self)._slave_ID is None or type(self)._uart is None:
            raise RuntimeError(type(self).__name__ + ".setup(uart, slave_ID) must be called first.")
        
        # --- UART laden (fest) ---
        self._uart = type(self)._uart
        
        # --- Slave_ID laden (fest) ---
        self._slave_ID = type(self)._slave_ID
        
        # --- JSON-Daten (dict) laden (fest)  ---
        self.__datablock = type(self)._datablock 
        
        # --- cCRC8-Objekt anlegen ---
        self.__crc8 = cCRC8(b'\xD5') # Polynom 0xD5
        
        # --- Value-ID setzen ---
        self._value_ID = None
        self.value_ID = value_ID
    
    # --- Properties (read-only) ---    
    @property
    def slave_ID(self):
        return self._slave_ID
    
    @property
    def uart(self):
        return self._uart
    
    @property
    def value_ID(self):
        return self._value_ID
    
    # --- Setter: value_ID ---
    @value_ID.setter
    def value_ID(self, value_ID):
        """
        Setzt nach Prüfung die Value-ID und erzeugt automatisch die Frames.
        
        param: value_ID: String
        return: None
        """
        
        if isinstance(value_ID, str):
            address_and_len = self.__datablock.get(value_ID) # Daten für value_ID aus json (hier schon dict) auslesen
            
            if address_and_len is not None:
                self._value_ID = value_ID
                
                # --- Adresse auslesen (12 Bit) ---      
                address = address_and_len[1]
                
                # --- Adresse aufteilen ---
                self.__address_LSB = address & 0xFF          # 8 Bit LSB der Adresse (für Read, Response und Write)
                self.__adress_MSB = address >> 8             # 4 Bit MSB der Adresse (entspricht Byte für Response)
                
                # --- Adressbytes für Lesen und Schreiben erzeugen ---
                address_MSB_read = 0x40 | self.__adress_MSB  # 4 Bit: 0x4_ für Read  + 4 Bit MSB der Adresse
                address_MSB_write = 0x80 | self.__adress_MSB # 4 Bit: 0x8_ für Write + 4 Bit MSB der Adresse
                
                # --- Länge der Daten auslesen und Främelänge bestimmen ---
                self.__data_len = address_and_len[2]         # Anzahl Bytes der Nutzdaten
                self.__frame_len = self.__data_len + 7       # Anzahl Bytes für Schreib- und Antwortframe
                
                # --- CRC8 für Länge berechnen (für Read) ---
                crc_of_len = self.__crc8.calc(bytearray([self.__data_len]))
                
                # --- Read: Request-Frame ---
                self.__req_Frame = bytearray([
                    __STARTBYTE,
                    self.slave_ID,
                    self.__address_LSB,
                    address_MSB_read,
                    __FRAME_LEN_READ,
                    self.__data_len,
                    crc_of_len,
                    __ENDBYTE])
                
                # --- Write-Frame-Header (ohne Daten) ---
                self.__write_Frame = bytearray([
                    __STARTBYTE,
                    self.slave_ID,
                    self.__address_LSB,
                    address_MSB_write,
                    self.__frame_len])
            else:
                raise ValueError("value_ID " + value_ID + " not found")
        else:
            raise ValueError("value_ID is not type 'string'")
    
    
    # --- Methoden zur Kommunikation ---
    def request(self):
        """
        Sendet einen Request-Frame an den USV-Slave.
        
        param: None
        return: None
        """
        self._uart.flush() 
        self._uart.write(self.__req_Frame)

    def response(self):
        """
        Empfängt und prüft eine Antwort vom USV-Slave und gibt die Nutzdaten des ersten gefundenen Frames, der ok ist, zurück.
        Immer nach Request verwenden.
        
        param: None
        return: bytearray: Nutzdaten oder None
        """        
        frame = self._uart.read() # Timeout notwendig!
        
        # Ankommende Nachricht kann auch länger sein. Aber nicht kürzer als gültiger Frame
        if frame is None or len(frame) < (self.__frame_len):
            return None
        
        # Suche nur so lange, wie es noch möglich ist, dass der gesamte Frame vorhanden ist.
        # Prüfe, wenn Daten gefunden wurden, immer die folgenden Werte
        for i in range(len(frame) - (self.__frame_len-1)):
            # --- Startbyte gefunden ---
            if frame[i] != __STARTBYTE:
                continue
            
            # --- Slave-ID gefunden ---
            if frame[i+1] != self._slave_ID:
                continue
            
            # --- Adresse LSB gefunden ---
            if frame[i+2] != self.__address_LSB:
                continue
            
            # --- Adresse MSB gefunden ---
            if frame[i+3] != self.__adress_MSB:
                continue
            
            # --- Främelänge gefunden ---
            if frame[i+4] != self.__frame_len:
                continue
    
            # --- Endbyte gefunden ---
            if frame[i+self.__frame_len-1] != __ENDBYTE:
                continue
                
            # --- Daten extrahieren ---
            raw_data = frame[(i+5):i+5+self.__data_len]
            crc_frame = frame[i+5+self.__data_len]
            
            # --- CRC8 prüfen ---
            if self.__crc8.calc(raw_data) == crc_frame:
                return raw_data # Nutzdaten als Bytearray zurückgeben
            
        # Keinen passenden Frame gefunden
        return None


    def write(self, data):
        """
        Sendet Daten an den USV-Slave.

        :param data (bytearray): Nutzdaten mit korrekter Länge
        :return: True wenn ACK empfangen. Sonst False.
        """        

        if isinstance(data, bytearray) and len(data) == self.__data_len:
            
            # --- Frame zusammensetzen ---
            frame = self.__write_Frame + data + bytearray([
                self.__crc8.calc(data),
                __ENDBYTE]) # extend hier nicht verwenden!

            self._uart.write(frame)
            
            # --- ACK prüfen --- 
            answ = self._uart.read()
        
            if answ is not None and answ[0] == 0xA1:
                return True
            else:
                return False
        else:
            raise ValueError("data is not a bytearray with " + str(self.__data_len) + " Bytes")
            
        
# --- Testprogramm ---
if __name__ == "__main__":
    from machine import UART, Pin
    import utime
    
    # Feste Slave ID
    SLAVE_ID = const(0x07)
    
    TIMEOUT_USV_DATA_MS = const(55) # Minimum 55ms für Matlabtestcode
    
    # UART0 init
    baudrate=250000
    uart0 = UART(0,
                 baudrate=baudrate, bits=8, parity=1, stop=1,
                 tx=Pin(0), rx=Pin(1), cts=Pin(2), rts=Pin(3),
                 timeout=TIMEOUT_USV_DATA_MS, timeout_char=1)
    
    USV_data.setup(slave_ID = SLAVE_ID, uart = uart0)
    USV_Bus = USV_data(value_ID = 'AS1')
    USV_Bus.request()
    data = USV_Bus.response()

    if data is not None:
        print('Data for ' + USV_Bus.value_ID,':', [hex(b) for b in data])
    else:
        print('No data for ' + USV_Bus.value_ID)
    
    data = bytearray([1,255])
    if USV_Bus.write(data):
        print('Write of ' + str(data) + ' for ' + USV_Bus._value_ID + ' was successful')
    else:
        print('Write of ' + str(data) + ' for ' + USV_Bus.value_ID + ' was not successful')
    
    USV_Bus.value_ID = 'AS2'
    USV_Bus.request()
    data = USV_Bus.response()

    if data is not None:
        print('Data for Value_ID', USV_Bus.value_ID,':', [hex(b) for b in data])
    else:
        print('No data for:', USV_Bus.value_ID)
    
    data = bytearray([1,128])
    if USV_Bus.write(data):
        print('Write of ' + str(data) + ' for ' + USV_Bus._value_ID + ' was successful')
    else:
        print('Write of ' + str(data) + ' for ' + USV_Bus.value_ID + ' was not successful')
    
    USV_Bus.value_ID = 'ER7'
    USV_Bus.request()
    data = USV_Bus.response()

    if data is not None:
        print('Data for Value_ID', USV_Bus.value_ID,':', [hex(b) for b in data])
    else:
        print('No data for:', USV_Bus.value_ID)
    
    data = bytearray([1])
    if USV_Bus.write(data):
        print('Write of ' + str(data) + ' for ' + USV_Bus._value_ID + ' was successful')
    else:
        print('Write of ' + str(data) + ' for ' + USV_Bus.value_ID + ' was not successful')
    
    USV_Bus.value_ID = 'SB1'
    USV_Bus.request()
    data = USV_Bus.response()

    if data is not None:
        print('Data for Value_ID', USV_Bus.value_ID,':', [hex(b) for b in data])
    else:
        print('No data for:', USV_Bus.value_ID)