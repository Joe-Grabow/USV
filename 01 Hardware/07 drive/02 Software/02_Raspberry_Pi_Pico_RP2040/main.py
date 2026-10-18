"""
Main Module

Created on 2026-03-26

Program history:
26.03.2026    V. 01.00    Initiale Version (Author: C. Händel)

Description:
- lädt das Hauptprogramm und ermöglicht Abbrüche

@author: C. Händel
"""

try:
    # Hauptprogramm: /drive_main.py
    import drive_main
        
except KeyboardInterrupt:
    # Unterbrechung durch Host-Computer (z. B. CTRL+C oder Thonny-STOP)
    print("Programmcode mit CTRL+C oder STOP beendet")
except Exception as error:
    # Ausgabe der Fehlermeldung
    print("Fehler:", error)