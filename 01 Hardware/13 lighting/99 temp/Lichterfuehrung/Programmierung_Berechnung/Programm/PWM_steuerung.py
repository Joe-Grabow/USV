# Libraries
from machine import Pin, ADC, PWM, UART
from utime import sleep_ms, sleep
from rp2 import StateMachine

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

Schaltfrequenzpwm =config["PWM_Sensor"]["feq"]
    
    
def PWM_G(duty):		#PWM Grün
    PWM_1 = PWM(Pin(config["PWM_Sensor"]["green"]))	#PWM für Grün
    PWM_1.freq(Schaltfrequenzpwm)
    PWM_1.duty_u16(duty)
    return
    
def PWM_W1(duty):
    PWM_2 = PWM(Pin(config["PWM_Sensor"]["white1"]))	#PWM für W1
    PWM_2.freq(Schaltfrequenzpwm)
    PWM_2.duty_u16(duty)
    return  
    
def PWM_W2(duty):
    PWM_3 = PWM(Pin(config["PWM_Sensor"]["white2"]))	#PWM für W2
    PWM_3.freq(Schaltfrequenzpwm)
    PWM_3.duty_u16(duty)
    return

def PWM_R(duty):
    PWM_4 = PWM(Pin(config["PWM_Sensor"]["red"]))	#PWM für Rot
    PWM_4.freq(Schaltfrequenzpwm)
    PWM_4.duty_u16(duty)
    return