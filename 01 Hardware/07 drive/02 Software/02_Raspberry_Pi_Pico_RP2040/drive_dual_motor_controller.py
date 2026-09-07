"""
Dual Motor Controller Module

Created on 2026-03-27

Program history:
27.03.2026    V. 01.00    Initiale Version (Author: C. Händel)

Description:
- beinhaltet die Kommunikation zu zwei ATtiny Motorcontrollern (Backbord, Steuerbord)
- PWM-Werte [0, 255] werden an beide Controller übertragen
- Steuerbord wird über Bluetooth angesteuert (mit Verzögerung)
- Backbord wird direkt angesteuert (UART / PIO)
- zeitversetztes Senden zur Kompensation der Bluetooth-Latenz
- Statusüberwachung beider Motorcontroller
- Kombination der Statuswerte in ein Byte für ESB

@author: C. Händel
"""

__version__ = '01.00'
__author__ = 'C. Händel'

import utime
from machine import Timer
from micropython import const
from drive_ATtiny_motor_communication import ATtinyMotorCommunication, STATE_OK
from drive_system_Haswing_Protuar import STOP_PWM

# --- Konstanten ---
BT_DELAY_MS = const(39)    # Durchschnittliche Verzögerung Bluetooth Steuerbord
SEND_INTERVAL = const(80)  # Intervall bis zum nächsten Senden. Max. Latenz von Bluetooth: 63 ms + Verarbeitunsgzeit und Puffer
                           # Neue Regler-Werte alle 100ms, aber falls Main-loop länger dauert, wird senden bereits vorher ermöglicht

class DualMotorController:
    """
    Verwaltung von zwei Motorcontrollern vom Typ ATtiny85 (Backbord / Steuerbord)
    - PWM-Signale senden
    - zeitliche Synchronisation
    - Statusüberwachung
    """
    
    # --- Init ---
    def __init__(self, uart_tx_port, uart_rx_port, uart_tx_starboard, uart_rx_starboard):
        """
        Initialisierung des Dual_Motor_Controllers
        - UARTs können Hardware- oder PIO-UART sein.
        
        param: uart_tx_port: UART TX Backbord
        param: uart_rx_port: UART RX Backbord
        param: uart_tx_starboard: UART TX Steuerbord
        param: uart_rx_starboard: UART RX Steuerbord
        return: None
        """
        
         # ATtiny Backbord (direkt)
        self._Attiny_port = ATtinyMotorCommunication(uart_tx = uart_tx_port, uart_rx = uart_rx_port)
        
        # ATtiny Steuerbord (Bluetooth)
        self._Attiny_starboard = ATtinyMotorCommunication(uart_tx = uart_tx_starboard, uart_rx = uart_rx_starboard)
        
        # PWM Ausgangswerte (Start = Stillstand)    
        self._port_PWM_to_send = STOP_PWM
        self._starboard_PWM_to_send = STOP_PWM
       
        # Statusvariablen
        self._state_port = None
        self._state_starboard = None
        
        # Timing für das das Senden des nächsten Werts (Bleutooth-Max. + Puffer)       
        self._last_starboard_send_time = 0
        

    # --- Properties ---
    @property
    def port_PWM_to_send(self):
        return self._port_PWM_to_send
    
    @port_PWM_to_send.setter
    def port_PWM_to_send(self, port_PWM_to_send):
        if isinstance(port_PWM_to_send, int): # Prüfe, ob Wert integer ist
            self._port_PWM_to_send = min(max(port_PWM_to_send, 0), 255) # Begrenze Werte auf 0 bis 255
        else:
            raise ValueError('port value is not an integer')
    
    @property
    def starboard_PWM_to_send(self):
        return self._starboard_PWM_to_send
    
    @starboard_PWM_to_send.setter
    def starboard_PWM_to_send(self, starboard_PWM_to_send):
        if isinstance(starboard_PWM_to_send, int): # Prüfe, ob Wert integer ist
            self._starboard_PWM_to_send = min(max(starboard_PWM_to_send, 0), 255) # Begrenze Werte auf 0 bis 255
        else:
            raise ValueError('starboard value is not an integer')
    
    @property
    def state_port(self):
        return self._Attiny_port.state
    
    @property
    def state_starboard(self):
        return self._Attiny_starboard.state
    
    @property
    def send_in_progress(self):
        return self._send_in_progress

    # --- Methoden ---    
    def update_state(self):
        """
        Aktualisiert den Status beider ATtiny-Controller
        
        param: None
        return: bool: True, wenn sich ein Status geändert hat
        """
        return self._Attiny_port.update_state() | self._Attiny_starboard.update_state()
    
    
    def check_state_ok(self):
        """
        Prüft, ob beide Attinys und deren Motoren fehlerfrei arbeiten
        
        param: None
        return: bool
        """
        if (self._Attiny_port.state == STATE_OK and
            self._Attiny_starboard.state == STATE_OK):
        
            return True
        else:
            return False


    def send_PWM_values(self):
        """
        Sendet PWM-Werte an beide Attiny-Microcontroller
        
        Ablauf:
        - Steuerbord zuerst (Bluetooth)
        - danach Backbord mit Verzögerung, um Latenz auszugleichen
        - erneutes Senden wartet auf die maximale Bluetooth-Latenzzeit + Puffer
        
        Hinweis:
        - delay ist hier zwar "dirty", aber die beste Lösung für das Gesamtkonzept, da die Motoren sehr träge sind
        - Hardware-Timer wurde getestet, konkurriert aber mit anderen Interrupts in der SBUS.py, wodurch
          die Timer-Callback-Funktion ab einen bestimmten Punkt nicht mehr ausgelöst wurde.
        - per utime.ticks_diff() war auch keine gute Lösung, da die Main-Loop sehr schwankend ist und dadurch die Werte
          mit sehr unterschiedlichem Timing-Abstand rausgesendet werden
        
        param: None
        return: None
        """
        
        # aktuelle Zeit einlesen
        timestamp = utime.ticks_ms()

        # Prüfe Sendintervall       
        if utime.ticks_diff(timestamp, self._last_starboard_send_time) >= SEND_INTERVAL:
            
            # Steuerbord (ATtiny über Bluetooth)
            self._Attiny_starboard.send_byte(self._starboard_PWM_to_send)
            
            # Letzte Sendezeit setzen
            self._last_starboard_send_time = timestamp 
        
            # Warte bis Bluetooth fertig
            utime.sleep_ms(BT_DELAY_MS)            
            
            # Backbord (ATtiny ohne Bluetooth)
            self._Attiny_port.send_byte(self._port_PWM_to_send)


    # --- Testfunktion ---
    def _state_reset(self):
        """
        Setzt Status beider Controller auf OK (nur Test!)
        
        param: None
        return: None
        """
        self._Attiny_port._state = STATE_OK
        self._Attiny_starboard._state = STATE_OK
          
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
    
    # Steuerbord (Bluetooth)
    uart1 = UART(1, baudrate=baudrate, bits=8, parity=None, stop=1, tx=Pin(4), rx=Pin(5))
    
    # Backbord TX (PIO)
    uart2_tx = UART_PIO_DMA_TX(statemachine=0, dmaChannel=0, tx_pin=Pin(26), baud=baudrate)
    
    # Backbord RX (PIO)
    uart2_rx = UART_PIO_DMA_RX(statemachine=1, dmaChannel=1, rx_pin=Pin(27), buffer_size = 10, baud=baudrate)
    uart2_rx.active(1)
    
    # --- Controller Initialisierung ---
    Dual_MC = DualMotorController(
        uart_tx_port = uart2_tx,
        uart_rx_port = uart2_rx,
        uart_tx_starboard = uart1,
        uart_rx_starboard = uart1)
    
    # Testvariablen
    cnt_test_err = 0
    
    #Testfunktion
    def all_PWM_values():
        for i in range(256):
            Dual_MC.update_state()
            Dual_MC.port_PWM_to_send = i
            Dual_MC.starboard_PWM_to_send = i
            print("port_PWM_to_send:", Dual_MC.port_PWM_to_send, "starboard_PWM_to_send:", Dual_MC.starboard_PWM_to_send)
            Dual_MC.send_PWM_values()
            utime.sleep_ms(50)
    
    try:
        # --- Haupt-Testschleife ---
        while True:
            # Status aktualisieren
            if Dual_MC.update_state():
                print("Status geupdatet")
                
            # Test: zyklischer Status-Reset
            if Dual_MC.state_port is not None and Dual_MC.state_starboard is not None:
                if cnt_test_err >=20:
                    cnt_test_err=0
                    Dual_MC._state_reset()
                else:
                    cnt_test_err+=1
                    
            # Statusausgaben        
            print("Status ok?:", Dual_MC.check_state_ok())
            print("Status Port:", Dual_MC.state_port)
            print("Status Starboard:", Dual_MC.state_starboard)
            print("port_PWM_to_send", Dual_MC.port_PWM_to_send)
            Dual_MC.port_PWM_to_send = 90
            Dual_MC.starboard_PWM_to_send = 90
            
            # Senden
            Dual_MC.send_PWM_values()
            utime.sleep_ms(5)
            
    except KeyboardInterrupt:
        print("Abbruch")