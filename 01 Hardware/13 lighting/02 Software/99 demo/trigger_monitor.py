# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 08:56:52 2025
@author: Joe Grabow (grabow@amesys.de)
"""
__version__ = '1.0'
__author__ = 'Joe Grabow'


"""
Der Trigger Monitor überprüft ob sich im Dictionary 'trigger' ein Eintrag 
geändert hat (ckeck_changes). Mögliche Einträge sind 'True' oder 'False'.
Hat sich ein Eintrag geändert (trigger_action), wird das geänderte
Dictionary zurückgegeben.   
"""
class TriggerMonitor:
    def __init__(self, initial_state):
        self.previous_state = initial_state.copy()
    
    def check_changes(self, current_state):
        if self.previous_state != current_state:  # Statusänderung
            self.previous_state = current_state.copy()  # alter Status = neuer Status
            return current_state  # neuer Triggerstatus
        return None  # keine Änderung der Trigger
    

"""
Funktion zur eigentlichen Ermittlung der Trigger. Hier müssen die Abfragen
nach sunset, sunrise, anchor, drive, usw. integriert werden. Außerdem dürfen 
keine Widersprüche auftreten z.B.: drive=True AND anchor=True
Als Testfunktion wird zunächst die Tastatureingabe benutzt.
"""
def Triggers(trigger_state):
    key_mapping = {
        "1": "drive",
        "2": "anchor",
        "3": "sunset",
        "4": "sunrise",
        "5": "light",
        "6": "dark",
        "7": "W1",
        "8": "W2",
        "9": "RG",
        "0": "Bus"
    }
    
    toggle_pairs = {
        "1": "2",
        "2": "1",
        "3": "4",
        "4": "3",
        "5": "6",
        "6": "5"
    }    
    
    eingabe = input("Trigger (Nummer eingeben): ")
    
    # Überprüfen, ob die Eingabe gültig ist
    if eingabe in key_mapping:
        # Setze den entsprechenden Trigger auf True
        ausgewählter_trigger = key_mapping[eingabe]
        trigger_state[ausgewählter_trigger] = True
        
        # bei gekoppelter Aktivierung / Deaktivierung
        if eingabe in toggle_pairs:
            trigger_state[key_mapping[toggle_pairs[eingabe]]] = False
        
    else:
        print("Ungültige Eingabe. Bitte eine Nummer zwischen 1 und 0 eingeben.") 
    
    return trigger_state


# für Testzwecke
if __name__ == "__main__":
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

    # Erstellung des Monitors
    monitor = TriggerMonitor(trigger)

    # Trigger über die Funktion setzen
    trigger = Triggers(trigger)


    # Änderungen überprüfen
    result = monitor.check_changes(trigger)
    if result is not None:
        print("Es gab Änderungen:", result)
    else:
        print("Keine Änderungen.")






