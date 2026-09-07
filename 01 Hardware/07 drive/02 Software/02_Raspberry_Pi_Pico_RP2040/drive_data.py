"""
Drive Data Module

Created on 2026-03-26

Program history:
26.03.2026    V1.00    Initiale Version (C. Händel)

Description:
- drive-Slave-Schnittstelle für die Bus-Kommunikation per UART
- Hardware-UART zwingend mit:
  (baudrate=250000, bits=8, parity=1, stop=1, timeout, timeout_char)
- Liest Vorschub(Trust), Richtung(Rudder) und Stop-Zustände
- Umrechnung der Busdaten in Q1.15 Format [-1, 1]
- Setzt drive-ESB-Fehlerbyte
- Behandelt Kommunikationsfehler und Timeout-Zustände

@author: C. Händel
"""

__version__ = '1.00'
__author__ = 'C. Händel'

# --- Imports ---
import utime
from micropython import const
from USV_data import USV_data

# --- Konstanten ---
# Feste Slave-ID für drive
SLAVE_ID = const(0x07) 

# Daten-IDs
GESB_ID = const('SB1')
TRUST_ID = const('AS1')
RUDDER_ID = const('AS2')
ESB_ID = const('ER7')

# Maximum für Zähler
MAX_CNT_NO_DATA = const(20)
MAX_CNT_ESB_SEND_FAILED = const(5)

# Bit 7 für den Status der Fernbedienung
RC_BIT = const(0x80)

# Zeit bis zum erneuten Versuch, ESB zu senden
RETRY_TIME_MS = const(5000)


class drive_data:
    """
    Schnittstelle zur Bus-Kommunikation für Drive-Daten:
    - Lesen von trust / rudder / stop
    - Schreiben des ESB-Status
    - Fehler- und Timeout-Behandlung
    """
    
    # --- Initialisierung ---
    def __init__(self, uart):
        """
        Initialisiert die Bus-Kommunikation

        param: uart (UART): Hardware-UART mit definierten Timeout und
                            (baudrate=250000, bits=8, parity=1, stop=1)
        return: None
        """
        # USV_data-Klasse vorbereiten. Feste Werte, die sich nicht ändern.
        USV_data.setup(SLAVE_ID, uart)
        
        # Effizienter für jede ID ein Objekt anzulegen, da vor Anfrage nichts mehr berechnet werden muss. Benötigt jedoch mehr Speicherplatz
        # Alternativ kann ein Objekt USV_data angelegt werden, bei dem die ID jedes Mal geändert wird. Weniger Speicherplatz, dafür ineffizienter. 
        self.__GESB_data = USV_data(value_ID = GESB_ID)
        self.__trust_data = USV_data(value_ID = TRUST_ID)
        self.__rudder_data = USV_data(value_ID = RUDDER_ID)
        self.__ESB_drive = USV_data(value_ID = ESB_ID)
        
        # Alten ESB-status auslesen, falls gesetzt:
        # Auslesen vor jedem Schreiben ist nicht nötig, da nur drive-Slave Schreibrechte hat.
        ESB_drive_data = self.__raw_data__(self.__ESB_drive)
        
        if ESB_drive_data is not None:       
            self.__ESB_drive_old = ESB_drive_data[0] # Setze den alten ESB-Wert zum späteren überpüfen.
        else:
            self.__ESB_drive_old = 0x00              # Bei keiner Antwort
        
        self._ESB_drive = self.__ESB_drive_old       # Neuer ESB Wert der geschrieben werden soll
        
        # Ausgaben
        self._GESB_drive_Bit = False                 # Zustand des Bits 0x80 aus dem GESB
        self._trust = None
        self._rudder = None
        
        # Fehlerzähler
        self._cnt_no_data = 0 
        self._cnt_send_ESB_failed = 0
        
        # Zustandsvariablen
        self._no_bus_connection = False              # Daten nach Fehlerversuchen nicht erhalten
        self.__no_bus_connection_changed = False     # Änderung am Status der Busverbindung
        self._ESB_send_aborted = False               # ESB senden nach Fehlversuchen abgebrochen
        
        # Timervariable
        self.__ESB_last_send_try = 0                 # Zeit, zu der das ESB-Senden abgebrochen wurde.

    # --- Properties ---
    @property
    def ESB_drive(self):
        return self._ESB_drive
    
    @property
    def GESB_drive_Bit(self):
        return self._GESB_drive_Bit

    @property
    def trust(self):
        return self._trust

    @property
    def rudder(self):
        return self._rudder
    
    @property
    def cnt_no_data(self):
        return self._cnt_no_data

    @property
    def cnt_send_ESB_failed(self):
        return self._cnt_send_ESB_failed
    
    @property
    def no_bus_connection(self):
        return self._no_bus_connection
    
    @property
    def ESB_send_aborted(self):
        return self._ESB_send_aborted

    
    # --- Öffentliche Methoden ---
    def get_data(self):
        """
        Liest Daten vom Bus: GESB, Trust und Rudder
        - Prüft als erstes ob das Bit 7 des GESB gesetzt ist.
        - Wenn nicht, werden die weiteren Daten abgefragt.
        - Falls keine Daten erhalten, wird nach x Fehlversuchen Status für keine Busverbindung gesetzt
        
        param: None
        return: bool: True = Daten erhalten, False = keine Daten
        """
        # --- Interne Funktionen ---
        # Zählt Fehlversuche, Daten zu erhalten oder setzt Status
        def cnt_failed_data_or_set_state():
            if self._cnt_no_data < MAX_CNT_NO_DATA:
                self._cnt_no_data += 1
            else: # Bus ausgefallen. Status setzen
                if self._no_bus_connection is False:
                    self.__no_bus_connection_changed = True
                    self._no_bus_connection = True
        
        # Setzt den Status für fehlerhaften Bus zurück
        def reset_failed_data_state():
            self._cnt_no_data = 0
            
            # Falls Status für Busfehler gesetzt, zurücksetzen
            if self._no_bus_connection:
                self.__no_bus_connection_changed = True
                self._no_bus_connection = False
                                    
        GESB = self.__raw_data__(self.__GESB_data)

        if GESB is not None:
            # Zähler für fehlerhaften Empfang hier noch nicht zurücksetzen.
            # Sonst bleiben Werte der Fernbedienung erhalten,
            # falls nur GESB, aber keine Trut und Rudder-Werte empfangen wurden.
            
            # Bit 7 entspricht dem drive_Bit. Falls gesetzt, keine weiteren Abfragen nötig.
            if GESB[0] & 0x80:
                self._GESB_drive_Bit = True
                
                # Empfang fertig. Status und Zähler zurücksetzen
                reset_failed_data_state()
                return True
            
            else:
                self._GESB_drive_Bit = False
                
                # Hole trust und rudder vom Bus und konvertiere in Q1.15 Nummern-Format
                self._trust = self.__get_Q_1_15__(self.__raw_data__(self.__trust_data))
                if self._trust is not None: # Zweite Anfrage, nur wenn erste erfolgreich war
                    self._rudder = self.__get_Q_1_15__(self.__raw_data__(self.__rudder_data))
                
                # Prüfe nochmal, ob Daten wirklich gesetzt wurden
                if self._trust is None or self._rudder is None:
                    cnt_failed_data_or_set_state()
                    return False
                else:
                    # Empfang fertig. Status und Zähler zurücksetzen
                    reset_failed_data_state()
                    return True
        else:
            # Keine Daten
            self._trust = None
            self._rudder = None
            
            cnt_failed_data_or_set_state()
            return False


    def update_ESB_drive(self, starboard_state, port_state, rc_lost: bool):
        """
        Bildet aus den Statuswerten den kombinierten Status als ESB
        
        param: starboard_state (byte), port_state (byte) , rc_lost (bool)
        return: None
        """
        # Einzelne Statuswerte vorbereiten
        if starboard_state is None:
            starboard_state = 0  # Noch nicht initialisiert
        elif not (isinstance(starboard_state, int) and starboard_state <= 0x0F and starboard_state >= 0x00):
            raise ValueError('starboard_state is not a byte from 0 to 15')
        
        if port_state is None:
            port_state = 0  # Noch nicht initialisiert
        elif not (isinstance(port_state, int) and port_state <= 0x0F and port_state >= 0x00):
            raise ValueError('port_state is not a byte from 0 to 15')

        # Kombiniertes Byte erstellen: obere 4  = Starboard, untere 4 Bit = port
        combined_state = (starboard_state << 4) | port_state
        
        if rc_lost:
            self._ESB_drive = RC_BIT | combined_state
        else:
            self._ESB_drive = ~RC_BIT & combined_state


    def send_ESB_drive(self):
        """
        Schreibt den drive-ESB-Status auf dem Bus.
            # LSB:
                # Bit 0: 0x01: Backbord: Keine Antwort von ATtiny
                # Bit 1: 0x02: Backbord: Motor sendet kein Start-Signal
                # Bit 2: 0x04: Backbord: Fehler im laufenden Betrieb von Motor
                # Bit 3: 0x08: nicht vergeben!
            # MSB:
                # Bit 4: 0x10: Steuerbord: Keine Antwort von ATtiny
                # Bit 5: 0x20: Steuerbord: Motor sendet kein Start-Signal
                # Bit 6: 0x40: Steuerbord: Fehler im laufenden Betrieb von Motor
                # Bit 7: 0x80: Fernbedienung Verbindung verloren!
        
        - Wiederholt x Versuche im Fehlerfall bis zum endgültigen Abbruch.
        - dann wird ESB-Sendefehler gesetzt
        
        param: ESB_drive_new (int): neues ESB-Byte
        return: bool:
            True  = Schreiben erfolgreich / bereits gesetzt
            False = Keine Verbindung bzw. Schreiben fehlgeschlagen
        """
        
        # 1. ESB bereits gesetzt
        if self.__ESB_drive_old == self._ESB_drive:
            self.reset_ESB_send_error()
            return True

        # 2. Senden bereits abgebrochen. Kein erneuter Versuch.
        # Es sei denn Verbindungssatus hat sich geändert oder Zeit für erneuten Versuch ist da.
        if self._ESB_send_aborted:
            if (self.__bus_connection_change_to_ok__() or
                (utime.ticks_diff(utime.ticks_ms(), self.__ESB_last_send_try) >= RETRY_TIME_MS)):
                self.reset_ESB_send_error()
            else:
                return False
            
        # 3. Schreiben versuchen
        if self.__ESB_drive.write(bytearray([self._ESB_drive])):
            self.reset_ESB_send_error()
            self.__ESB_drive_old = self._ESB_drive
            return True
        
        # 4. Fehlerfall
        if self._cnt_send_ESB_failed < MAX_CNT_ESB_SEND_FAILED:
            self._cnt_send_ESB_failed += 1
        else: # endgültig abbrechen 
            self._ESB_send_aborted = True # Setze Abbruch-Status für spätere Auswertungen
            self.__ESB_last_send_try = utime.ticks_ms()
        return False
            
    
    def reset_ESB_send_error(self):
        """
        Setzt den ESB-Sendefehler zurück.
        
        param: None
        return: None
        """
        self._ESB_send_aborted = False
        self._cnt_send_ESB_failed = 0
        self.__ESB_last_send_try = 0


    # --- Interne Methoden ---
    def __raw_data__(self, USV_data_obj):
        """
        Führt Anfrage und Antwort aus und gibt erhalte Daten weiter
        
        param: USV_data_obj: Anfrageobjekt
        return: bytes | None
        """
        USV_data_obj.request()
        return USV_data_obj.response()

    def __get_Q_1_15__(self, raw_data):
        """
        Ermittelt aus den erhaltenen Daten das Q1.15 Format
        
        param: raw_data (bytearray(2)): [0]: LSB; [1]: MSB; Reihefolge = [1], [0]
        return: float | None
        """
        if raw_data is not None:
            # Prüfe erstes Bit des MSB auf negativen Werte
            if (raw_data[1] & 0x80): 
                dec=-1
            else:
                dec=0
                
            # Bestimme die Nachkommazahl    
            frac=(((raw_data[1] & 0x7F)<<8) + raw_data[0])/2**15
             
            return dec + frac
        else:
            return None
        
    def __bus_connection_change_to_ok__(self):
        """
        Prüf, ob die Verbindung nach einem Fehlerfall beim Lesen wieder ok ist.
        
        param: None
        return: bool:
            True  = Status wieder ok
            False = Status nicht ok oder keine Änderung
            
        """
        bus_ok = False
        
        if self.__no_bus_connection_changed and self._no_bus_connection is False:
            bus_ok = True
        
        self.__no_bus_connection_changed = False # Flag resetten.
        return bus_ok


# Test
if __name__ == "__main__":
    from machine import UART, Pin
    TIMEOUT_USV_DATA_MS = const(55) # Minimum 55ms für Matlabtestcode
    
    # --- UART0 init ---
    baudrate=250000
    uart0 = UART(0, baudrate=baudrate, bits=8, parity=1, stop=1, tx=Pin(0), rx=Pin(1), cts=Pin(2), rts=Pin(3), timeout=TIMEOUT_USV_DATA_MS, timeout_char=1)    
    
    # --- Objekt ---
    data = drive_data(uart0)
    
    print(data.__get_Q_1_15__(bytearray([0,128])))
    
    try:
        while True:
            if data.get_data():
                if data.GESB_drive_Bit:
                    print('Fehler Not-Halt erkannt')
                    port=90 # Setze Not-Stop
                    starboard=90 # Setze Not-Stop
                else:
                    print('Trust:', data.trust, ', Rudder:', data.rudder)
            else:
                print('Keine Daten vom Bus erhalten.')
            
            if data.ESB_send_aborted:
                print("Sende-Abbruch")
                #data.reset_ESB_send_error()

            data.update_ESB_drive(0x01,0x02,rc_lost = True)
            print(bin(data.ESB_drive))
            data.send_ESB_drive()
            
    except KeyboardInterrupt:
        print("Abbruch")