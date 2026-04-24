# Libraries
from machine import Pin, ADC

from collections import deque
from utime import sleep_ms, sleep

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

class MovingAverage:
    def __init__(self, size=20):
        self.size = size
        self.values = deque(maxlen=size)  # FIFO-Queue für die letzten 'size' Werte

    def add_value(self, new_value):
        """Fügt einen neuen Wert hinzu"""
        self.values.append(new_value)  # Neuen Wert zur Liste hinzufügen
    
    def get_average(self):
        """Gibt den aktuellen Mittelwert zurück (ohne neue Werte hinzuzufügen)"""
        return sum(self.values) / len(self.values) if self.values else 0  # Vermeidet Division durch 0

R_average = MovingAverage(config["adc_sensors"]["Value_avg_cnt"])
W1_average = MovingAverage(config["adc_sensors"]["Value_avg_cnt"])
W2_average = MovingAverage(config["adc_sensors"]["Value_avg_cnt"])
G_average = MovingAverage(config["adc_sensors"]["Value_avg_cnt"])

def Average_queue():
    
    while True:
        G_average.add_value(read_ADC_G)
        R_average.add_value(read_ADC_R)
        W1_average.add_value(read_ADC_W1)
        W2_average.add_value(read_ADC_W2)
        #sleep_ms(config["adc_sensors"]["time_ms"])

def ADC_R_average():    
    R_avg = R_average.get_average
    return R_avg
    
def ADC_W1_average():  
    W1_avg = W1_average.get_average
    return W1_avg
    
def ADC_W2_average():
    W2_avg = W2_average.get_average
    return W2_avg
    
def ADC_G_average():
    G_avg = G_average.get_average
    return G_avg

def read_ADC_R():
    adc_1 = ADC(Pin(config["adc_sensors"]["ADC_R"]["pin"]))    # Photodiode Rot                                                                                                                                                                                                                                                                                                                                                                                  
    adc_1.read_u16()        #
    return adc_1

def read_ADC_G():
    adc_4 = ADC(Pin(config["adc_sensors"]["ADC_G"]["pin"]))    # Photodiode Grün
    adc_4.read_u16()        #
    return adc_4
    
def read_ADC_W1():
    adc_2 = ADC(Pin(config["adc_sensors"]["ADC_W1"]["pin"]))    # Photodiode W1
    adc_2.read_u16()        #
    return adc_2
    
def read_ADC_W2():
    adc_3 = ADC(Pin(config["adc_sensors"]["ADC_W2"]["pin"]))    # Photodiode W2
    adc_3.read_u16()        #
    return adc_3
