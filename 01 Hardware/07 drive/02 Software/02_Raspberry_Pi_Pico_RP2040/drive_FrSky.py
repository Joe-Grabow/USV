"""
FrSky RC Control Module

Created on 2026-03-26

Program history:
26.03.2026    V01.00    Initiale Version (Autor: C. Händel)

Description:
- Liest SBUS-Daten einer FrSky-Fernbedienung über PIO-UART
- Dekodiert Vorschub(Trust)- und Richtungs(Rudder)-Werte
- Prüft Failsafe-Status und Schalterstellung für Regler
- Enthält Timeout-Mechanismus bei Verbindungsverlust

@author: C. Händel
"""

__version__ = '01.00'
__author__ = 'C. Händel'

import utime
from SBUS import SBUSDecoder

# --- Konstanten ---
TIMEOUT_MS = 1000 # Timeoutzeit bei fehlenden SBUS-Daten


# --- FrSky Klasse ---
class FrSkyRC:    
    # --- Init ---
    def __init__(self, uart):
        """
        Initialisiert die FrSkyRC-Klasse

        param: uart (UART_RX): SBUS-PIO-UART Objekt für SBUS-Empfang
        return: None
        """
        # --- UART prüfen ---
        if type(uart).__name__ == 'UART_RX':
            self.__uart = uart
        else:
            raise ValueError('No UART_RX from SBUS')
        
        # --- Internes Objekt ---
        self.__SBUS = SBUSDecoder()
        
        # --- Ausgangswerte ---
        self._trust = 0
        self._rudder = 0
        self._PID_Control_On = True # Schalter für Reglersteuerung
        self._On = False            # Fernbedienung aktiv (False = aus)
        
        # --- Verbindunsstatusvariablen
        self._last_update = 0                 # Letzter gültiger Empfang für Timeout
        self._lost_connection = False         # Status für Verbindungsabbruch der Fernbedienung
        self._lost_connection_changed = False # Flag, ob sich Status für Verbindungsabbruch geändert hat
                                              # Sofort nach dem RC_Check auslesen, um die Änderung mitzubekommen.
    
    # --- Properties ---
    @property
    def trust(self):
        return self._trust
    
    @property
    def rudder(self):
        return self._rudder
    
    @property
    def PID_Control_On(self):
        return self._PID_Control_On
    
    @property
    def On(self):
        return self._On

    @property
    def lost_connection(self):
        return self._lost_connection

    @property
    def lost_connection_changed(self):
        return self._lost_connection_changed
        
    # --- Check- und Update-Funktion ---
    def check_RC_Control(self):
        """
        Prüft neue SBUS-Daten und aktualisiert Steuerwerte.
        Hinweis:
        - Nach Start sendet die Fernbedienung zunächst keine SBUS-Daten.
        - Demnach kann UART-Buffer nicht voll sein, wodurch auch kein
          Failsafe ausgelesen werden kann.
        - Erst nach dem An- und Wieder-Ausschalten wird Failsafe gesendet

        param: None
        return: bool: True, Daten erhalten, False wenn keine
        """
        
        timestamp = utime.ticks_ms()
        
        # --- Prüfen, ob kompletter SBUS-Datensatz vorhanden ---
        if self.__uart.buffer.is_full():
            
            # Status für Verbindungsabbruch zurücksetzen, falls gesetzt
            if self._lost_connection:
                self._lost_connection = False
                self._lost_connection_changed = True  # Flag kurzzeitig setzen
            else:
                self._lost_connection_changed = False # Flag zurücksetzen
            
            # Rohdaten aus Puffer holen
            data = self.__uart.get_data()
            
            # Vollständigen SBUS-Frame suchen
            sbus_frame = self.__SBUS.find_frame(data)
            
            if sbus_frame:
                # Letzte Updatezeit festhalten (für Timeouterkennung)
                self._last_update = timestamp         
                
                # --- Failsafe prüfen ---
                failsafe_active = self.__SBUS.get_sbus_flags(sbus_frame, 1)
                
                if failsafe_active is False:
                    # Fernbedienung aktiv
                    self._On = True

                    # --- Kanal 14: Umschalter RC oder Regler ---
                    # >= 0 (Schwellwert, falls Wert driftet): RC aktiv
                    if self.__SBUS.get_normed_value(
                        self.__SBUS.get_sbus_channel(sbus_frame, 14)
                        ) >= 0: 
                        
                        # --- RC-Steuerung aktiv (Regler aus) ---
                        self._PID_Control_On = False

                        # Kanal 1: Vorschub (Trust)
                        self._trust = self.__SBUS.get_normed_value(
                            self.__SBUS.get_sbus_channel(sbus_frame, 1))
                        
                        # Kanal 2: Richtung (Rudder)
                        self._rudder = self.__SBUS.get_normed_value(
                            self.__SBUS.get_sbus_channel(sbus_frame, 2))
                        
                    else:
                        # --- Regler aktiv (RC aus) ---
                        self._PID_Control_On = True
                else:
                    # --- Failsafe aktiv: Fernbedienung aus ---
                    self._On = False
                    
            # --- UART für nächsten Empfang zurücksetzen ---
            self.__uart.restart()
            
            # SBUS-Daten gefunden
            return True
        
        # --- Kein neuer Frame: Timeout prüfen ---
        else:
            # Timeout erst prüfen, wenn überhaupt einmal Daten empfangen wurden, Status noch nicht gesetzt wurde
            if self._last_update != 0 and self._lost_connection is False:
                if utime.ticks_diff(timestamp, self._last_update) > TIMEOUT_MS:
                    # --- Bei Verbindungsverlust: Sichere Zustände setzen ---
                    self._trust = 0
                    self._rudder = 0
                    self._PID_Control_On = True
                    self._On = False
                    
                    # Flag für Verbindungsabbruch setzen und last_update-Zeit auf 0 setzen
                    self._lost_connection = True
                    self._lost_connection_changed = True
                    self._last_update = 0
            else:
                self._lost_connection_changed = False
            
            # Keine SBUS-Daten gefunden
            return False


# Test
if __name__ == "__main__":
    from machine import Pin
    import utime
    from SBUS import UART_RX as SBUS_UART
    
    BAUD_SBUS = 100000
    uart3_rx = SBUS_UART(statemachine=4, rx_pin=Pin(5), baud=BAUD_SBUS) # Statemachine muss größer 3 sein, sonst Speicherfehler
    uart3_rx.activate(1)  # State Machine aktivieren
    
    FrSky = FrSkyRC(uart3_rx)
    utime.sleep_ms(20) # Zeit nach dem Einschalten, dass die Daten der Fernbedienung empfangen werden können
    
    try:
        while True:
            FrSky.check_RC_Control()  # Testfunktion
            
            if FrSky.lost_connection_changed:
                print("RC_status_Update")
            utime.sleep_ms(250)
    except KeyboardInterrupt:
        print("Abbruch")