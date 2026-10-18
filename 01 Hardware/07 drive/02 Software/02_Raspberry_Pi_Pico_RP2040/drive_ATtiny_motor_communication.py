# Beinhaltet alle Funktionen für die Kommunikation zu den ATtiny85
"""
ATtiny Motor Communication Module

Created on 2026-03-27

Program history:
27.03.2026    V. 01.00    Initiale Version (Author: C. Händel)

Description:
- beinhaltet die Kommunikation zu einem ATtiny85 Motorcontroller
- Senden von PWM-Werten [0, 255] über UART oder PIO-UART
- Auswertung empfangener Statusbytes des Motors
- Erkennung folgender Zustände:
    - Motor OK
    - kein Startsignal
    - Fehler im laufenden Betrieb
    - keine Antwort (Timeout)
- Fehler werden gezählt und erst nach mehrfacher Bestätigung gesetzt
- Status wird zur Weiterverarbeitung bereits bitweise gesetzt

@author: C. Händel
"""

__version__ = '01.00'
__author__ = 'C. Händel'


import utime
from micropython import const

# --- Motor-Zustandsantworten ---
MOTOR_OK = const(0xAA)
MOTOR_NOT_OK = const(0xBB)
MOTOR_NOT_MORE_OK = const(0xCC)

# --- Statuswerte (Bitgrößen) ---
STATE_OK = const(0x00)              # Attiny sendet OK
STATE_NO_RESPONSE = const(0x01)     # Keine Antwort vom ATtiny
STATE_NO_START_SIGNAL = const(0x02) # Fehler des des Motors beim Start
STATE_RUNTIME_ERROR = const(0x04)   # Fehler des Motors im laufenden Betrieb

# --- Zeitkonstanten ---
TIMEOUT_START_MS = const(30000)  # Timeout nach dem Start, um bei Nicht-Antwort Fehler zu setzen
TIMEOUT_RX_MS = const(1000)      # Timeout für nicht erhaltene Werte

#--- Fehlerzähler ---
MAX_CNT_ERROR = const(5) # Anzahl wie, of eine Fehler von den Motoren empfangen werden muss, bis dieser gesetzt wird


class ATtinyMotorCommunication:
    """
    Kommunikation mit einem ATtiny Motorcontroller:
    - Senden von PWM-Werten als Steuerbytes
    - Empfangen und Auswerten von Statuswerten
    """
    
    def __init__(self, uart_tx, uart_rx):
        """
        Initialisierung der UART-Schnittstellen
        
        param: uart_tx: UART TX (Hardware oder PIO)
        param: uart_rx: UART RX (Hardware oder PIO)
        return: None
        """
        
        # Tx-UART prüfen
        if type(uart_tx).__name__ in ('UART', 'UART_PIO_DMA_TX'): 
            self._uart_tx = uart_tx
        else:
            raise ValueError('No UART or UART_PIO_DMA_TX for Tx')
        
        # Rx-UART prüfen
        if type(uart_rx).__name__ in ('UART', 'UART_PIO_DMA_RX'): 
            self._uart_rx = uart_rx
        else:
            raise ValueError('No UART or UART_PIO_DMA_RX for RX')
               
        # Statusvariable
        # None bis Timeout oder erster gültiger Kommunikation
        self._state = None
        
        # Zeit-Varibalen
        self._start_time = utime.ticks_ms()
        self._last_rx_time = None
        
        # Fehlerzähler
        self._cnt_error = 0

    # --- Properties ---    
    @property
    def state(self):
        return self._state

    # --- Öffentliche Methoden ---
    def send_byte(self, byte):
        """
        Sendet ein Byte an den ATtiny
        
        param: byte (int): Wert [0, 255]
        return: None
        """
        
        if type(self._uart_tx).__name__ == 'UART':
            self._uart_tx.write(bytearray([byte]))
        else:
            self._uart_tx.write(bytearray([byte]), cnt=1) # 1 Byte Größe
        
    def update_state(self):
        """
        Liest UART-Daten vom ATtiny85 und aktualisiert den Status
        Antworten:
            # keine Antwort vom ATtiny
            # 0xAA: Motor ist ok
            # 0xBB: Fehler des des Motors beim Start
            # 0xCC: Fehler des Motors im laufenden Betrieb
        zu setzender Status:
            # 0x00: Attiny sendet OK
            # 0x01: Keine Antwort von ATtiny
            # 0x02: Motor sendet kein Start-Signal
            # 0x04: Fehler im laufenden Betrieb vom Motor
        
        param: None
        return: bool: True, wenn sich der Status geändert hat
        """
        
        state_changed = False
        
        # UART auslesen und letzen empfangenen Wert zurückgeben
        rx_byte = self._read_uart_last_byte(self._uart_rx)
        
        # Empfangenes Byte auf validen Wert prüfen
        checked_value = self._check_for_valid_value(rx_byte)
        
        # Neuen Status ermitteln
        new_state = self._get_new_state(checked_value)
        
        # Bei Änderung Status setzen
        if new_state is not None and self._state != new_state: 
            self._state = new_state
            state_changed = True
        
        return state_changed
                    
##########################################################################################
    # Interne Funktion, die nur in check_and_update_state benötigt werden.
##########################################################################################
    # --- Interne Methoden (nur für update_state())---
    def _read_uart_last_byte(self, uart):
        """
        Liest Daten vom zugewiesenen UART und gibt, falls vorhanden, den letzten Wert zurück
        
        param: uart: UART oder UART_PIO_DMA_RX
        return: byte | None
        """
        data = None
        cnt = 0
        
        if type(uart).__name__ == 'UART':
            if uart.any():
                data = uart.read()
                cnt = len(data)
                
        elif type(uart).__name__ == 'UART_PIO_DMA_RX':
            if uart.ready():
                data, cnt = uart.get_buffer()
                
        if data is not None:
            return data[cnt-1]
        else:
            return None
        
    def _check_for_valid_value(self, byte):
        """
        Prüft letztes empfangenes Byte auf gültige Statuswerte
        
        param: byte
        return: int | None
        """
        
        if byte in (MOTOR_OK, MOTOR_NOT_OK, MOTOR_NOT_MORE_OK):
            return byte
        else:
            return None
    
    def _get_new_state(self, value):
        """
        Ermittelt neuen Status basierend auf empfangenen Wert
        
        param: value (int | None)
        return: int | None
        """
        
        timestamp = utime.ticks_ms()
        
        # Keine validen Werte erhalten
        if value == None:
            # Prüfe Timeout nach Start
            if self._state is None: 
                if utime.ticks_diff(timestamp, self._start_time) > TIMEOUT_START_MS: 
                    return STATE_NO_RESPONSE
                
            # Prüfe Timeout im laufenden Betrieb
            else:
                if utime.ticks_diff(timestamp, self._last_rx_time) > TIMEOUT_RX_MS:
                    return STATE_NO_RESPONSE
        
        # Validen Wert erhalten
        else:
            self._last_rx_time = timestamp
            
            if value == MOTOR_OK:
                self._cnt_error = 0 
                return STATE_OK
            else:
                if self._cnt_error < MAX_CNT_ERROR:
                    self._cnt_error += 1
                else:
                    if value == MOTOR_NOT_OK:
                        return STATE_NO_START_SIGNAL
                    else: # value == MOTOR_NOT_MORE_OK
                        return STATE_RUNTIME_ERROR

        return None # wenn Zähler hochgezählt wird und keine Statusänderung stattfand
    
    # --- Testfunktion ---
    def _state_reset(self):
        """
        Setzt Status auf OK (nur Test!).
        Sonst nicht im Code verwenden!
        
        param: None
        return: None
        """
        self._state = STATE_OK
        
##########################################################################################    
# Test
if __name__ == "__main__":
    from machine import UART, Pin
    import utime
     
    from pio.uart_dma_tx import UART_PIO_DMA_TX
    from pio.uart_dma_rx import UART_PIO_DMA_RX
    
    baudrate=9600
    
    # --- Startup Delay ---
    #  - ATtiny und Bluetooth senden beim Start Störsignale (z. B. 0x00),
    #    die fälschlich als gültige Daten interpretiert werden können.
    #  - Delay verhindert fehlerhafte Auswertung
    utime.sleep_ms(2000)
    
    # --- UART Initialisierung ---
    uart1 = UART(1, baudrate=baudrate, bits=8, parity=None, stop=1, tx=Pin(4), rx=Pin(5))
    
    uart2_tx = UART_PIO_DMA_TX(statemachine=0, dmaChannel=0, tx_pin=Pin(26), baud=baudrate)
    
    uart2_rx = UART_PIO_DMA_RX(statemachine=1, dmaChannel=1, rx_pin=Pin(27), buffer_size = 10, baud=baudrate)
    uart2_rx.active(1)
    
    # --- Objekt ---
    ATtinyMotor = ATtinyMotorCommunication(
        uart_tx = uart2_tx,
        uart_rx = uart2_rx)
    
    # Testvariablen
    test_ok = False
    cnt_test_err = 0
     
    try:     
        while True:
            
            # Simulation von Statuswerten
            if ATtinyMotor.state is not None:
                if test_ok is False:
                    ATtinyMotor._read_uart_last_byte = lambda rx_uart: b'\x00\xAA'[-1]
                    test_ok = True
                else:
                    ATtinyMotor._read_uart_last_byte = lambda rx_uart: b'\x00\xBB'[-1]
                    
                    if cnt_test_err >=20:
                        test_ok = False
                        cnt_test_err=0
                    else:
                        cnt_test_err+=1
            
            # Status aktualisieren
            if ATtinyMotor.update_state():
                print("Status geupdatet")

            print ("Status:", ATtinyMotor.state)

            # Test-Senden
            ATtinyMotor.send_byte(90)
            utime.sleep_ms(50)
            
    except KeyboardInterrupt:
        print("Abbruch")