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
import ADC
import uart

import json

CONFIG_FILE = "config.json"

def load_config(filename=CONFIG_FILE):
    """Lädt die Konfiguration aus einer JSON-Datei"""
    try:
        with open(filename, "r") as file:
            return json.load(file)  # JSON-Daten als Dictionary laden
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Konfigurationsdatei nicht gefunden oder fehlerhaft.")
        return None  # Falls Fehler auftreten, None zurückgeben
# 🔹 Konfiguration laden
config = load_config()
if not config:
    raise SystemExit  # Beende das Programm, falls die Konfiguration fehlt
    
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
    
    Vergleichswerte = {          #werte nach berechnung/test setzen
        "Ausfall_W": config["Trigger_monitor"]["white"],
        "Ausfall_R": config["Trigger_monitor"]["red"],
        "Ausfall_G": config["Trigger_monitor"]["green"],
        "Schwellwert_dark": config["Trigger_monitor"]["dark"],
        "Schwellwert_light": config["Trigger_monitor"]["light"]
    }
    
    Value_ADC_R = ADC_R_average
    Value_ADC_G = ADC_G_average
    Value_ADC_W1 = ADC_W1_average
    Value_ADC_W2 = ADC_W1_average
    Value_anchor = UART_read_bus(anker)
    
    if ( Value_ADC_R < Ausfall_R)||(VAlue_ADC_G < Ausfall_G):
        trigger_state[9] =True
        
    if Value_ADC_W1 < Ausfall_W:   
        trigger_state[7] =True
        
    if Value_ADC_W2 < Ausfall_W:   
        trigger_state[8] =True 
        
    if sum(1 for wert in [Value_ADC_W1,Value_ADC_W2,Value_ADC_G,Value_ADC_R]if wert < Schwellwert_dark ) >=3:   
        trigger_state[6] =True
        trigger_state[key_mapping[toggle_pairs[6]]] = False
        
    if sum(1 for wert in [Value_ADC_W1,Value_ADC_W2,Value_ADC_G,Value_ADC_R]if wert < Schwellwert_light ) >=3:   
        trigger_state[5] =True
        trigger_state[key_mapping[toggle_pairs[5]]] = False
        
    if  Value_anchor = True   
        trigger_state[2] =True
        trigger_state[key_mapping[toggle_pairs[1]]] = False
     if  Value_anchor = True   
         trigger_state[1] =True
         trigger_state[key_mapping[toggle_pairs[2]]] = False
    
    return trigger_state
