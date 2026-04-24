# -*- coding: utf-8 -*-
"""
Created on Sun Mar 23 13:49:22 2025

@author: Samuro75
"""
from machine import UART
from machine import Pin

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

UART_BAUDRATE = config["Uart"]["BAUDRATE"]
uart = UART(1, baudrate=UART_BAUDRATE, tx=Pin(config["Uart"]["tx_pin"]), rx=Pin(config["Uart"]["rx_pin"]), bits=8, parity=None, stop=1)

# slave ID einfügen

#anfragen von daten
# 1 0xa5 start 
# 2 0xXX slave ID
# 3 0xXX adrr LSB  
# 4 0x4X addr MSB
# 5 0x08 frame lenge
# 6 0xXX datenläne 
# 7 0xXX CRC-8 von der Datenlänge
# 8 0xA6 Ende
"""
Slave_id = 40
adr_LSB = 0
adr_LSB = 0
Data_length=0
CRC=0
Fram_length=0
Data=0
"""
send_r = bytearray([xA5,config["Uart"]["Slave_id"],adr_LSB,adr_MSB,x08,Data_length,CRC,xA6])	#Datenlesen vom bus
send_w = bytearray([xA5,config["Uart"]["Slave_id"],adr_LSB,adr_MSB,Fram_length,Data,CRC,xA6])	#Daten schreiben vom bus


def crc8_d5_byte(byte):
    poly = 0xD5
    crc = byte
    for _ in range(8):
        if crc & 0x80:
            crc = (crc << 1) ^ poly
        else:
            crc <<= 1
        crc &= 0xFF
    return crc


def UART_read_bus(data):
    match data:
        case Longitude :        #x001
            adr_LSB = config["Uart"]["read"]["Longitude"]["LSB"]
            adr_MSB = config["Uart"]["read"]["Longitude"]["MSB"]
            Data_length = config["Uart"]["read"]["Longitude"]["len"]
            CRC = crc8_d5_byte(Data_length)
            uart.write(send_r)
            Data_Buffer=bytearray(uart.read())
            Longitude_4= Data_Buffer[6]
            Longitude_3= Data_Buffer[7]
            Longitude_2= Data_Buffer[8]
            Longitude_1= Data_Buffer[9]
            Longitude=(Longitude_1<<24|Longitude_2<<16|Longitude_3<<8|Longitude_4)
            
            return Longitude
        
        case Latitude :         #x005
            adr_LSB = config["Uart"]["read"]["Latitude"]["LSB"]
            adr_MSB = config["Uart"]["read"]["Latitude"]["MSB"]
            Data_length = config["Uart"]["read"]["Latitude"]["len"]
            CRC = crc8_d5_byte(Data_length)
            uart.write(send_r)
            Data_Buffer=bytearray(uart.read())
            Latitude_4= Data_Buffer[6]
            Latitude_3= Data_Buffer[7]
            Latitude_2= Data_Buffer[8]
            Latitude_1= Data_Buffer[9]
            Latitude=(Latitude_1<<24|Latitude_2<<16|Latitude_3<<8|Latitude_4)
            return Latitude
        
        case time:              #x00E
            adr_LSB = config["Uart"]["read"]["time"]["LSB"]
            adr_MSB = config["Uart"]["read"]["time"]["MSB"]
            Data_length = config["Uart"]["read"]["time"]["len"]
            CRC = crc8_d5_byte(Data_length)
            uart.write(send_r)
            Data_Buffer=bytearray(uart.read())
            time_3= Data_Buffer[6]
            time_2= Data_Buffer[7]
            time_1= Data_Buffer[8]
            time =(time_1<<16|time_2<<8|time_3)
            return time
        
        case date :                 #kein datum auf dem Bus verfügbar
           adr_LSB = config["Uart"]["read"]["date"]["LSB"]
           adr_MSB = config["Uart"]["read"]["date"]["MSB"]
           Data_length = config["Uart"]["read"]["date"]["len"]
           CRC =crc8_d5_byte(Data_length)
           #uart.write(send_r)
           #Data_Buffer=bytearray(uart.read())
           #date = Data_Buffer[6]
            
            return #date
        
        case anker:             #x124
            adr_LSB = config["Uart"]["read"]["anker"]["LSB"]
            adr_MSB = config["Uart"]["read"]["anker"]["MSB"]
            Data_length = config["Uart"]["read"]["anker"]["len"]
            CRC = crc8_d5_byte(Data_length)
            uart.write(send_r)
            Data_Buffer=bytearray(uart.read())
            Anker = Data_Buffer[6]
            return anker
    return
"""
LED Status auf dem Bus:
    x00 - initial state
    x01 - 1&W2 off; Error W; R/G off
    x02 - W2 full; W1 Fail; R/G off
    x03 - W1 full; W2 Fail; R/G off
    x04 - R/G off ;Error R/G ; W1/W2  on half

    
    x12 - W2 full; W1 Fail; R/G on
    x13 - W1 full; W2 Fail; R/G on
    x14 - W1/W2  on half; R/G on
    
    x21 - R/G off ;W1/W2  on half
"""
def UART_write_bus(LED_Status):
    adr_LSB = config["Uart"]["write"]["LSB"]
    adr_MSB = config["Uart"]["write"]["MSB"]
    Data = LED_Status
    Fram_length = 8 
    CRC = crc8_d5_byte(Data)
    uart.write(send_w)
    return