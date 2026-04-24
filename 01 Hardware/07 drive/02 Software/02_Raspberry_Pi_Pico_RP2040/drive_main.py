"""
Drive Main Module

Created on 2026-03-26

Program history:
26.03.2026    V. 01.00    Initiale Version (Author: C. Händel)

Description:
- beinhaltet den kompletten drive-Ablauf mit Zuständen und Zustandsübergängen
- RP Pico ist bei der Backbord-Seite (Port)
- Ablauf (zyklisch):
    1. Motoren und Attiny-Verbindungen prüfen
    2. ESB prüfen und ggf. senden
    3. Fernbedienung prüfen und mit Fernbedienung steuern
    4. Buskommunikation prüfen und mit Reglerwerten steuern
    5. PWM-Werte berechnen
    6. PWM-Werte an beide Attinys senden
    7. Bei Stopbit, Busaufall oder Motoren-/ATtiny-Fehler: Stoppen

# --- Zustandsdiagramm ------------------------------------------------------------------
#                        __
#                       |  |(Motoren nicht OK)                 
#                       V  |
#     /------------- 0: Stop <---------------------\
#     |                   |                        |
#     |                   |(Motoren OK && RC aus)  |
#     |(Motoren OK        \-----------------\      | 
#     | && RC an)                           |      |(Busausfall | Stopbit erhalten)
#     |                (RC an)              |      |
#     |      /-------------------------\    |      |
#     |      |                         |    |      |
#     V      V                         |    V      /
# 1: Fernbedienung                 2: Reglerbetrieb 
#            |                              ^
#            |     (RC aus / Ausfall)       |    
#            \------------------------------/       
#
# ---------------------------------------------------------------------------------------

TODO:
- Ablauf derzeit über if-else-Zweige realisiert
- Für bessere Nachvollziehbarkeit: State machine implementieren:
    STATE_STOP = const(0)           # Stop
    STATE_RC = const(1)             # Fernbedienung aktiv
    STATE_BUS = const(2)            # Regler aktiv


@author: C. Händel
"""

__version__ = '01.00'
__author__ = 'C. Händel'

# --- uC Imports ---
from machine import UART, Pin
import utime
from micropython import const

# --- Kommunikations-Imports ---
from pio.uart_dma_tx import UART_PIO_DMA_TX
from pio.uart_dma_rx import UART_PIO_DMA_RX
from SBUS import UART_RX as SBUS_UART

# --- Drive-Module ---
from drive_data import drive_data
from drive_FrSky import FrSkyRC
from drive_system_Haswing_Protuar import Drive_System_Haswing_Protuar, STOP_PWM
from drive_dual_motor_controller import DualMotorController

# --- Konstanten ---
BAUD_USV = const(250000)        # Baudrate USV-Slave
BAUD_ATTINY = const(9600)       # Baudrate beide ATTiny85
BAUD_SBUS = const(100000)       # Baudrate SBUS (FrSky)

TIMEOUT_USV_DATA_MS = const(10) # Timeout für UART.read der USV-Busabfrage.
                                # (min: 11 Bit x 1/250.000 Baud * 8 Bytes = 352 us)
                                # (+ Bearbeitungszeiten und Puffer: 10 ms)
                                # (Für Matlabtestcode minimal 55 ms notwendig)
TIMEOUT_CHAR_USV_MS = const(2)  # Timeout-Char für UART.read der USV-Busabfrage.
                                # (min: 11 Bit x 1/250.000 Baud = 44 us)
                                # (+ Bearbeitungszeiten und Puffer: 2 ms)

# --- UART-Inits ---
# --- UART0: USV-Slave ---
#  - Muss Hardware-UART sein (PIO-UART funktioniert nicht).
#  - Timeout für Rx-Abbruch ist erforderlich, beeinflusst aber die Hauptschleife
uart0 = UART(0, baudrate=BAUD_USV, bits=8, parity=1, stop=1,
             tx=Pin(0), rx=Pin(1), cts=Pin(2), rts=Pin(3),
             timeout=TIMEOUT_USV_DATA_MS, # Timeout für Rx
             timeout_char=TIMEOUT_CHAR_USV_MS)

# --- UART1: Bluetooth-Modul für Steuerbord (auch PIO möglich) ---
uart1 = UART(1, baudrate=BAUD_ATTINY, bits=8, parity=None, stop=1,
             tx=Pin(8), rx=Pin(9))

# --- UART2: ATtiny Backbord (PIO-UART) (auch Hardware-UART möglich) ---
uart2_tx = UART_PIO_DMA_TX(
    statemachine=0,
    dmaChannel=0,
    tx_pin=Pin(26),
    baud=BAUD_ATTINY)

# Achtung: PIO-Rx sammelt ggf. Werte, bevor diese abegrufen werden können. Wichtig für Timeout!
# Z.B.: array('B', [170, 170, 170, 170, 170, 102, 102, 102, 102, 102]), Anzahl: 5
# nach 500 ms ausgegeben, obwohl alle 100 ms von ATtiny gesendet und somit auch empfangen.
uart2_rx = UART_PIO_DMA_RX(
    statemachine=1,
    dmaChannel=1,
    rx_pin=Pin(27),
    buffer_size = 10,
    baud=BAUD_ATTINY)
uart2_rx.active(1)    

# --- UART3 RX: SBUS (FrSky) ---
#  - muss SBUS_UART über PIO sein (kein Hardware-UART!)
#  - statemachine muss größer 3 sein, sonst Speicherfehler
uart3_rx = SBUS_UART(
    statemachine=4,
    rx_pin=Pin(5),
    baud=BAUD_SBUS) 
uart3_rx.activate(1)

# --- Objekt-Initialisierung ---
data = drive_data(uart0)               # Kommunikation USV-Slave (speziell drive-Slave)   
FrSky = FrSkyRC(uart3_rx)              # FrSky-Fernbedienung
DS_HP = Drive_System_Haswing_Protuar() # DriveSystem (speziell für Motoren Haswing Protuar)
Dual_MC = DualMotorController(         # Motor Controller für beide ATtiny85
    uart_tx_port = uart2_tx,
    uart_rx_port = uart2_rx,
    uart_tx_starboard = uart1,
    uart_rx_starboard = uart1)

# --- Hardware ---
led = Pin('LED', Pin.OUT)
    
# --- Hilfvariable für Timer aller Intervalle
next_times={}

# --- Hilfsfunktionen ---
def check_every_ms(interval):
    """
    Prüft, ob das gegebene Intervall in ms abgelaufen ist.
    next_times speichert die nächsten Ausführungszeitpunkte pro Intervall.
    
    param: interval: Intervall in ms
    param: next_times: Nächste interne Zeit je Intervall (default-Argument)
    return: True wenn Intervall erreicht 
    """
    timestamp = utime.ticks_ms()

    # Initialisierung, wenn Intervall noch nicht existiert
    if interval not in next_times:
        next_times[interval] = utime.ticks_add(timestamp, interval)
        return False

    # Prüfen, ob Zeit erreicht
    if utime.ticks_diff(timestamp, next_times[interval]) >= 0:
        next_times[interval] = utime.ticks_add(next_times[interval], interval)
        return True

    return False

def set_stop():
    """
    Setzt Not-Stopp für beide Motoren und toggelt LED langsam.
    
    param: None
    return: None
    """
    Dual_MC.port_PWM_to_send = STOP_PWM
    Dual_MC.starboard_PWM_to_send = STOP_PWM
    
    if check_every_ms(1000):
        led.toggle()

def PWM_values_update_and_set():
    """
    - Berechnet neue PWM-Werte und setzt diese zum Senden an beide ATtinys.
    - Erst wenn das Senden des zweiten Wertes abgeschlossen ist, sollen neue gesetzt werden.
    
    param: None
    return: None
    """ 
    DS_HP.update_PWM_values()

    Dual_MC.port_PWM_to_send = DS_HP.port_PWM
    Dual_MC.starboard_PWM_to_send = DS_HP.starboard_PWM


# --- Hauptschleife ---  
while True:            
    # Prüfen, ob Status der Attinys verändert wurde
    ATt_state_changed = Dual_MC.update_state()
    
    # Prüfe die Fernebdierung und update Werte
    FrSky.check_RC_Control()
    
    # Erstelle ESB neu, wenn eine Änderung der Fernbedienung oder ATtinys erkannt wurde
    if FrSky.lost_connection_changed or ATt_state_changed:            
        data.update_ESB_drive(port_state = Dual_MC.state_port,
                              starboard_state = Dual_MC.state_starboard,
                              rc_lost=FrSky.lost_connection)                
        
    # Sende ESB-Byte. Interne Logik prüft Statusänderung oder vorherigem Fehler beim Senden
    data.send_ESB_drive()
    
    
    # --- Beginn Zustandslogik- -------------------------------------------------------------------------------------
    # --- Zustandsprüfung der Attinys ---
    if Dual_MC.check_state_ok():
        
        # --- Fernbededienung --- (hat Vorrang vor Regler)
        if FrSky.On and FrSky.PID_Control_On is False: # Zustand 1: Fernbedienung (Reglerschalter aus)
            led.value(1)
            DS_HP.hysterese = 0.15 # damit USV auf der Stelle wenden kann
            
            # Berechne nur, wenn neue Werte erhalten wurden
            if DS_HP.trust != FrSky.trust or DS_HP.rudder != FrSky.rudder:
                DS_HP.trust = FrSky.trust
                DS_HP.rudder = FrSky.rudder
                PWM_values_update_and_set()
                
        else:                        
            # --- Busbetrieb ---
            if data.get_data():                    # USV-Slave-Verbindung ok
                if data.GESB_drive_Bit:            # Zustand 0 (vom Bus kommt Stop-Signal, Bit 7 von GESB):                     
                    set_stop()
                else:                              # Zustand 2: Reglerbetrieb
                    if check_every_ms(100):        # Regler-Verbindung anzeigen
                        led.toggle()
                    DS_HP.trust = data.trust
                    DS_HP.rudder = data.rudder
                    DS_HP.hysterese = 0            # Regler soll alle PWM-Werte fein ansteuern können.
                    PWM_values_update_and_set()
            else: 
                if data.no_bus_connection:         # Zustand 0 (Bus ausgefallen)
                    set_stop()
    else:                                          # Zustand 0 (Fehler der Attinys / Motoren)
        set_stop()                                 # Ermöglicht auch die Wiederaufnahme des Betriebs nach Ausfall            
    
    # --- Ende Zustandslogik- -----------------------------------------------------------------------------------------
    
    # --- Daten senden (auch ohne neu erhaltene Werte) ---
    #  - Sicherstellung von kontinuierlicher Steuerung und Not-Stopp
    Dual_MC.send_PWM_values()            