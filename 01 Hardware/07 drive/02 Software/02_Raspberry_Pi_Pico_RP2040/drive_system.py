"""
Created on Wed Oct 16 16:47:39 2024

Program history
17.10.2024    V. 00.01    Start mit Definition der Bewegungsfunktion (Author: Prof. Grabow)
22.06.2025    V. 01.00    getter, setter, update() und Description hinzugefügt. (Author: C. Händel)

Description:
- Basisklasse für Antriebslogik
- Input-Werte: trust, rudder (-1 bis +1) und hysterese (0 bis 0,5)
- Update-Funktion berechnet daraus die Steuerbefehle für Steuerbord und Backbord als normierte Werte (-1 bis +1)
@author: Prof. Grabow (grabow@amesys.de)
"""

__version__ = '01.00'
__author__ = 'Joe Grabow'

# drive_system.py

class DriveSystem:
    
    # --- Init ---
    def __init__(self):
        # Input
        self._trust = 0
        self._rudder = 0
        self._hysterese = 0
        
        # Output
        self._port = 0 # Backbord
        self._starboard = 0 # Steuerbord
        
    # --- Properties ---
    @property
    def trust(self):
        return self._trust
    
    @trust.setter
    def trust(self, trust):
        if isinstance(trust, (int, float)):
            self._trust = min(max(trust,-1),1)
    
    @property
    def rudder(self):
        return self._rudder
    
    @rudder.setter
    def rudder(self,rudder):
        if isinstance(rudder, (int, float)):
            self._rudder = min(max(rudder,-1),1)
    
    @property
    def hysterese(self):
        return self._hysterese
    
    @hysterese.setter
    def hysterese(self, hysterese):
        if isinstance(hysterese, (int,float)):
            self._hysterese = min(max(hysterese,0),0.5)
    
    @property
    def port(self):
        return self._port
    
    @property
    def starboard(self):
        return self._starboard
        
    # --- Update-Methode ---
    def update(self):
        """
        Berechnet die Backbord(Port)- und Steuerbord(Starboard)-Ausgänge basierend auf Trust, Rudder und Hysterese
        
        param: None
        return: None
        """
        if abs(self._trust) <= self._hysterese and self._hysterese!=0:  # Trust ist nahe 0
            self._port = self._rudder
            self._starboard = -self._rudder
        elif self._rudder > 0:
            self._port = self._trust
            self._starboard = (-2 * self._rudder + 1) * self._trust
        elif self._rudder < 0:
            self._port = (2 * self._rudder + 1) * self._trust
            self._starboard = self._trust
        else: # rudder = 0
            self._port = self._trust
            self._starboard = self._trust
    
# Test
if __name__ == "__main__":
    DS = DriveSystem()
    DS.rudder = 0.2
    DS.hysterese = 0.1
    
    for i in range (-100,101):
        DS.trust =-i/100
        DS.update()
        print('Trust:', DS.trust, 'Rudder:', DS.rudder, '; Port:', DS.port,', Starboard:', DS.starboard)