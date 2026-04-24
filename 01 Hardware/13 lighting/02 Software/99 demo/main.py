# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 13:34:44 2025

@author: Joe Grabow (grabow@amesys.de)
"""

__version__ = '1.0'
__author__ = 'Joe Grabow'

from state_machine import StateMachine  # State Machine
from user_state_functions import s_f_1, s_f_2, s_f_3, s_f_4  # alle Zustandsfunktionen
import trigger_monitor  # Trigger für die State Machine

# Initialisiere die State Machine
state_machine = StateMachine()

# Mögliche Trigger: 
# 1=drive, 2=anchor, 3=sunset, 4=sunrise, 5=light, 6=dark, 7=W1, 8=W2, 9=RG
# 0=Bus

# Initialisierung des Trigger-Dictionaries
trigger = {
    "drive": False,
    "anchor": False,
    "sunset": False,
    "sunrise": False,
    "light": False,
    "dark": False,
    "W1": False,
    "W2": False,
    "RG": False,
    "Bus": False
}

# Dictionary mit allen Zustandsfunktionen
state_functions = {
    1: s_f_1,
    2: s_f_2,
    3: s_f_3,
    4: s_f_4
}

# Erstellung des Triggermonitors
monitor = trigger_monitor.TriggerMonitor(trigger)

# Startzustand setzen und erste Funktion ausführen
current_state = 1  # Startzustand (drive)
state_functions[current_state](trigger)  # Starte mit 'Fahrt Tag'

# Hauptschleife
while True:
    try:
        trigger = trigger_monitor.Triggers(trigger)  # auf Trigger abfragen
        result = monitor.check_changes(trigger)  # auf Änderungen der Trigger prüfen
        if result is not None:  # Triggerzustand geändert
            current_state = state_machine.transition(current_state, result)  # Zustand wechseln
            
            # Zustandsfunktion aufrufen, falls definiert
            state_function = state_functions.get(current_state)  # Funktion abrufen

            if state_function:  # Falls der Zustand existiert
                state_function(result)
            else:
                print("State not defined")
            
        else:
            print("Keine Zustandsänderungen.") 


    except ValueError:
        print("Ungültige Eingabe! Bitte eine Zahl eingeben.")
            
            

