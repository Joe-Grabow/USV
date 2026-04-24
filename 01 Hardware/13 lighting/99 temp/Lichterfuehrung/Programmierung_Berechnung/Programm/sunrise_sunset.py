# -*- coding: utf-8 -*-
"""
Created on 23.01.2025
@author: Grabow

Berechnet aus den GPS-Koordinaten und dem Datum die Zeiten des
Sonnenaufganges und Sonnenunterganges (vereinfachte Berechnung)
"""
__version__ = '1.0'
__author__ = 'Joe Grabow'

import math
from datetime import datetime
from uart import UART_read_bus


def convert_decimaltime(decimal_time):
    """
    Konvertiert eine Dezimalzeit in das Stunden:Minuten-Format.
    
    Args:
        decimal_time (float): Zeit im Dezimalformat.
    
    Returns:
        time (str): Zeit im Format HH:MM.
    """

    stunden = int(decimal_time)
    minuten = int((decimal_time - stunden) * 60)
    time = f"{stunden:02d}:{minuten:02d}"
    return time

def day_of_year(year, month, day):
    """
    Berechnet den Tag des Jahres für ein gegebenes Datum (z. B. 1 = 1. Januar).

    Args:
        year (int): Jahr.
        month (int): Monat.
        day (int): Tag.

    Returns:
        day_number (int): Die Tageszahl des Jahres.
    """
    n1 = math.floor(275 * month / 9)
    n2 = math.floor((month + 9) / 12)
    n3 = (1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3))
    day_number = n1 - (n2 * n3) + day - 30
    return day_number

def calculate_hour_angle(is_rise_time, cosH):
    """
    Berechnet den Stundenwinkel basierend darauf, ob es Sonnenaufgang oder Sonnenuntergang ist.

    Args:
        is_rise_time (bool): True für Sonnenaufgang, False für Sonnenuntergang.
        cosH (float): Kosinus des Stundenwinkels.

    Returns:
        hour_angle (float): Stundenwinkel in Stunden.
    """
    hour_angle = math.degrees(math.acos(cosH))
    if is_rise_time:
        hour_angle = 360 - hour_angle
    return hour_angle / 15 # Stundenwinkel in Stunden umrechnen


def calculate_sun_time(latitude, longitude, date, zenith, is_rise_time):
    """
    Berechnet die UTC-Zeit für Sonnenaufgang oder Sonnenuntergang.

    Args:
        latitude (float): Breitengrad.
        longitude (float): Längengrad.
        date (int, int, int): Datum im Format (Jahr, Monat, Tag).
        zenith (float): Zenitwinkel für die Berechnung.
        is_rise_time (bool): True für Sonnenaufgang, False für Sonnenuntergang.

    Returns:
        sun_time (float): Uhrzeit des Sonnenereignisses in UTC.
    """
    year, month, day = date
    day_of_year_value = day_of_year(year, month, day)
    lng_hour = longitude / 15

    # Berechnungen für ungefähren Zeitwert
    t = day_of_year_value + ((6 if is_rise_time else 18) - lng_hour) / 24

    # Mittlere Anomalie
    M = (0.9856 * t) - 3.289

    # Wahre Sonnenlänge
    L = M + (1.916 * math.sin(math.radians(M))) + (0.020 * math.sin(math.radians(2 * M))) + 282.634
    L %= 360

    # Rektaszension
    RA = math.degrees(math.atan(0.91764 * math.tan(math.radians(L))))
    RA %= 360

    # Quadrantenkorrektur
    L_quadrant = (math.floor(L / 90)) * 90
    RA_quadrant = (math.floor(RA / 90)) * 90
    RA = RA + (L_quadrant - RA_quadrant)
    RA /= 15 # Rektaszension in Stunden

    # Deklination der Sonne
    sinDec = 0.39782 * math.sin(math.radians(L))
    cosDec = math.cos(math.asin(sinDec))

    # Stundenwinkel berechnen
    cosH = (math.cos(math.radians(zenith)) - (sinDec * math.sin(math.radians(latitude)))) / (cosDec * math.cos(math.radians(latitude)))

    # Prüfen, ob Sonnenaufgang oder -untergang möglich ist
    if cosH > 1 or cosH < -1:
        return None # Kein Sonnenaufgang/-untergang
  
    # Stundenwinkel berechnen
    H = calculate_hour_angle(is_rise_time, cosH)

    # Lokale mittlere Zeit berechnen
    T = H + RA - (0.06571 * t) - 6.622
    sun_time = (T - lng_hour) % 24 # UTC-Zeit
    return sun_time

def calculate_sunrise_sunset(latitude, longitude, date):
    """
    Berechnet die Sonnenaufgangs- und Sonnenuntergangszeiten in UTC.

    Args:
        latitude (float): Breitengrad.
        longitude (float): Längengrad.
        date (int, int, int): Datum im Format (Jahr, Monat, Tag).

    Returns:
        sunrise_utc,sunset_utc (float, float): Sonnenaufgangs- und Sonnenuntergangszeiten in UTC.
    """
    
    longitude   = UART_read_bus(Longitude)
    latitude    = UART_read_bus(Latitude)
    Loc_time    = UART_read_bus(time)
    date        = UART_read_bus(date)
    
    zenith = 90.833  # Ziviler Dämmerungswinkel
    sunrise_utc = calculate_sun_time(latitude, longitude, date, zenith, is_rise_time=True)
    sunset_utc = calculate_sun_time(latitude, longitude, date, zenith, is_rise_time=False)
    return sunrise_utc, sunset_utc

if __name__ == "__main__":
    # latitude = 52.5200  # Breite von Berlin
    # longitude = 13.4050  # Länge von Berlin
    # date = (2025, 5, 22)  # Datum: 20. März 2025 (Tag- und Nachtgleiche)

    

    # Ergebnisse für verschiedene Zenitwinkel anzeigen
    print(f"{'Sonnenaufgang':<18} {'Sonnenuntergang':<18}")

    sunrise, sunset = calculate_sunrise_sunset(latitude, longitude, date)
    if sunrise is not None and sunset is not None:
        print(f"{convert_decimaltime(sunrise):<18} {convert_decimaltime(sunset):<18}")
    else:
        print("Die Sonne geht an diesem Tag nicht auf oder unter.")
