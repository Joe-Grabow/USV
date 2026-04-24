# -*- coding: utf-8 -*-
"""
Created on Wed Nov 29 08:24:08 2023
@author: Grabow
"""
__version__ = '1.1'
__orinialauthor__ = 'Joe Grabow'
__editor___ = 'Jacob Rommel'


# Libraries
from PWM_steuerung import PWM_G, PWM_W1, PWM_W2, PWM_R
from uart import UART_write_bus

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

"""
LED Status auf dem Bus:
    x00 - initial state
    x01 - 1&W2 off; Error W; R/G off
    x02 - W2 full; W1 Fail; R/G off
    x03 - W1 full; W2 Fail; R/G off
    x04 - R/G off ;Error R/G ; W1/W2  on half

    x11 - 1&W2 off; Error W; R/G off
    x12 - W2 full; W1 Fail; R/G on
    x13 - W1 full; W2 Fail; R/G on
    x14 - R/G off ;Error R/G ; W1/W2  on half
    x15 - W1/W2  on half; R/G on
    
    x21 - R/G off ;W1/W2  on half
"""
##General Values         
    duty_cyle_W_N = config["u_statfunc"]["cyle_W_N"]	#Weis normal wert
    duty_cyle_W_P = config["u_statfunc"]["cyle_W_P"]	#weis Power wert
    duty_cyle_R_N = config["u_statfunc"]["cyle_R_N"]	#rot normal wert; 
    duty_cyle_G_N = config["u_statfunc"]["cyle_G_N"]	#grün normal wert

def drive_night(trigger):
    global output_set
    match trigger:
        case {"W1": True, "W2": True}:
            #print('LED W1 OFF')
            PWM_W1(0)
            #print('LED W2 OFF')
            PWM_W2(0)
            #print('Error W')
            UART_write_bus(x11)
        
        case {"W1": True, "W2": False}:
            #print('LED W2 full')
            PWM_W2(duty_cyle_W_P)
            PWM_W1(0)
            #print('Fail W')
            UART_write_bus(x12)
 
        case {"W2": True, "W1": False}:
            #print('LED W1 full')
            PWM_W1(duty_cyle_W_P)
            PWM_W2(0)
            #print('Fail W')
            UART_write_bus(x13)
 
        case {"RG": True}:
            #print('LED RG OFF')
            PWM_R(0)
            PWM_G(0)
            #print('Fail RG')
            UART_write_bus(x14)
    
        case _:
            #print('LED W1 half')
            PWM_W1(duty_cyle_W_N)
            #print('LED W2 half')
            PWM_W2(duty_cyle_W_N)    
            #print('LED RG ON')
            PWM_R(duty_cyle_R_N)
            PWM_G(duty_cyle_G_N)
            UART_write_bus(x15)
    return


def anchor_night(trigger):
    match trigger:
        case {"W1": True, "W2": True}:
            #print('LED W1 OFF')
            PWM_W1(0)
            #print('LED W2 OFF')
            PWM_W2(0)
            #print('Error W')
            UART_write_bus(x01)
        
        case {"W1": True, "W2": False}:
            #print('LED W2 full')
            PWM_W2(duty_cyle_W_P)
            PWM_W1(0)
            #print('Fail W')
            UART_write_bus(x02)
 
        case {"W2": True, "W1": False}:
            #print('LED W1 full')
            PWM_W1(duty_cyle_W_P)
            PWM_W2(0)
            #print('Fail W')
            UART_write_bus(x03)
 
        case {"RG": True}:
            #print('LED RG OFF')
            PWM_R(0)
            PWM_G(0)
            #print('Fail RG')
            UART_write_bus(x04)
    
        case _:
            #print('LED W1 half')
            PWM_2.duty_u16(duty_cyle_W_N)
            #print('LED W2 half')
            PWM_3.duty_u16(duty_cyle_W_N) 
            #print('LED RG OFF')
            PWM_R(0)
            PWM_G(0)
            UART_write_bus(x05)
    return


# all User-State-Functions
def s_f_1(trigger):  # Zustand 1
    global output_set
    if trigger["Bus"]:
        #print('\n','Busfehler')
        drive_night(trigger)
    else:    
        #print('\n','Fahrt Tag')
        #print('LED W1 OFF')
        PWM_W1(0)
        #print('LED W2 OFF')
        PWM_W2(0)
        #print('LED RG OFF')
        PWM_R(0)
        PWM_G(0)
        UART_write_bus(x00)
    return

def s_f_2(trigger):  # Zustand 2
    if trigger["Bus"]:
        #print('\n','Busfehler')
        drive_night(trigger)
    else: 
        #print('\n','Fahrt Nacht')
        drive_night(trigger)
    return

def s_f_3(trigger):  # Zustand 3
    if trigger["Bus"]:
        #print('\n','Busfehler')
        drive_night(trigger)
    else: 
        #print('\n','Anker Tag')
        #print('LED W1 OFF')
        PWM_W1(0)
        #print('LED W2 OFF')
        PWM_W2(0)
        UART_write_bus(x21)
    return

def s_f_4(trigger):  # Zustand 4
    if trigger["Bus"]:
        #print('\n','Busfehler')
        drive_night(trigger)
    else: 
        #print('\n','Anker Nacht')
        anchor_night(trigger)
    return

