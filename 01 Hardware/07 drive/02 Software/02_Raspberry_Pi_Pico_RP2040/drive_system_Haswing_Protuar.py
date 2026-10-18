"""
Drive System Haswing Protuar Module

Created on 2026-03-26

Program history:
26.03.2026    V. 01.00    Initiale Version (Author: C. Händel)

Description:
- beinhaltet die Steuerkennlinienberechnung Haswing Protuar
- ursprüngliche Eingangswerte der Kennlinie sind int16 [-16384, 16384]
- Kennlinie wird anhand dieser Werte auf normierte Eingangswerte [-1, 1] umgerechnet
- aus DriveSystem werden die Berechnungen der Steuerbefehle [-1, 1] übernommen
- aus Steuerbefehlen werden passende PWM-Werte [0, 255] als Ausgang berechnet
- Segmentbasierte Steuerkennlinie Haswing Protuar:
    - Segment 1: positive Leistung > 0: PWM [112, 235]
    - Segment 2: Stillstand (neutral):  PWM [69, 111]: (Mittelwert = 90)
    - Segment 3: negative Leistung < 0: PWM [24, 68]

@author: C. Händel
"""

__version__ = '01.00'
__author__ = 'C. Händel'

from micropython import const
from drive_system import DriveSystem

# --- Segment 2-Grenzwerte ---
__x_MAX_POWER_0__ = const(0.00390625) # (=64/16384) Oberer Grenzwert: entpricht PWM = 111
__x_MIN_POWER_0__ = -__x_MAX_POWER_0__ # (=-64/16384) Unterer Grenzwert: entpricht PWM = 69

# --- Geradengleichung für Segmente 1 und 3 (y = mx + n ) ---
__m1__ = const(123) # Anstieg für Segment 1:      x > __x_max_Power_0__
__n1__ = const(112) # Verschiebung für Segment 1: x > __x_max_Power_0__
__m3__ = const(45)  # Anstieg für Segment 2:      x < __x_min_Power_0__
__n3__ = const(69)  # Verschiebung für Segment 2: x < __x_min_Power_0__

# PWM-Wert für Neutralstellung des Motors
STOP_PWM = const(90)

# --- Drive_System_Haswing_Protuar Klasse ---
class Drive_System_Haswing_Protuar(DriveSystem):
    """
    Erweiterung des DriveSystem:
    - Übersetzt Port/Starboard-Ausgänge in PWM-Werte für Haswing Protuar Motoren
    """
    def __init__(self):
        # Input from DriveSystem (trust, rudder, hysterese)
        super().__init__() 
        
        # Output
        self._port_PWM = 0
        self._starboard_PWM = 0
    
    # --- Properties ---
    @property
    def port_PWM(self):
        return self._port_PWM
    
    @property
    def starboard_PWM(self):
        return self._starboard_PWM
    
    # --- Update Methode ---
    def update_PWM_values(self):
        """
        Berechnet die PWM-Ausgangswerte für beide Motoren.
        
        param: None
        return: None
        """
        super().update() # Berechnung der normierten Steuerbefehle (DriveSystem)
        
        self._port_PWM = self.__calculate_PWM_value__(self._port)
        self._starboard_PWM = self.__calculate_PWM_value__(self._starboard)

    def __calculate_PWM_value__(self, value: float):
        """
        Berechnet den PWM-Wert aus einem normierten Eingangswert.
        
        param: value(float): normierter Eingangswert [-1, 1]
        return: value(int): PWM-Wert für den Motor
        """
        if value < -1 or value > 1:
            raise ValueError('value is not float [-1, 1]')
        
        if value > __x_MAX_POWER_0__:
            value = value * __m1__ + __n1__
        elif value < __x_MIN_POWER_0__:
            value = value * __m3__ + __n3__
        else: # Stillstand. PWM wird auf 90 gesetzt
            value = STOP_PWM
        
        return int(value)
        
# Test
if __name__ == "__main__":
    DS_HP = Drive_System_Haswing_Protuar()
    DS_HP.rudder = 0.25
    DS_HP.hysterese = 0
    
    print(DS_HP.__calculate_PWM_value__(-1))
    
    for i in range (-100,101):
        DS_HP.trust = -i/100
        DS_HP.update_PWM_values()
        print('Trust:', DS_HP.trust, 'Rudder:', DS_HP.rudder, '; Port:', DS_HP.port_PWM,', Starboard:', DS_HP.starboard_PWM)