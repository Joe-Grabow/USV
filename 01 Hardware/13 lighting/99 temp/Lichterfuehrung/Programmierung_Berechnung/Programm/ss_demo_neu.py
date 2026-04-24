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

#zenith_values = [90.833, 90.7, 90.6, 90.5, 90.4, 90.3, 90.2, 90.1, 90]

def time_difference_in_minutes(decimal_time1, decimal_time2):
    """Berechnet die Zeitdifferenz in Minuten"""
    # Convert decimal times to HH:MM format
    time1 = convert_dezimalzeit(decimal_time1)
    time2 = convert_dezimalzeit(decimal_time2)
    
    # Convert time strings to datetime objects
    time_format = "%H:%M"
    t1 = datetime.strptime(time1, time_format)
    t2 = datetime.strptime(time2, time_format)

    # Calculate the time difference in minutes
    diff = abs((t2 - t1).total_seconds() / 60)
    
    # If the difference is greater than 12 hours, subtract from 24 hours
    if diff > 12 * 60:
        diff = 24 * 60 - diff
    
    return diff - 12*60

def convert_dezimalzeit(dezimalzeit):
    """Konvertiert Dezimalzeit in Stunden:Minuten-Format."""
    stunden = int(dezimalzeit)
    minuten = int((dezimalzeit - stunden) * 60)
    return f"{stunden:02d}:{minuten:02d}"

def day_of_year(year, month, day):
    """Berechnet den Tag des Jahres (z. B. 1 = 1. Januar)."""
    n1 = math.floor(275 * month / 9)
    n2 = math.floor((month + 9) / 12)
    n3 = (1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3))
    return n1 - (n2 * n3) + day - 30

def calculate_hour_angle(is_rise_time, cosH):
    """Berechnet den Stundenwinkel basierend darauf, ob es Sonnenaufgang oder Sonnenuntergang ist."""
    H = math.degrees(math.acos(cosH))
    if not is_rise_time:
        H = 360 - H
    return H / 15  # Stundenwinkel in Stunden umrechnen

def calculate_sun_time(latitude, longitude, date, zenith, is_rise_time):
    """Berechnet die UTC-Zeit für Sonnenaufgang oder Sonnenuntergang."""
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
    RA /= 15  # Rektaszension in Stunden

    # Deklination der Sonne
    sinDec = 0.39782 * math.sin(math.radians(L))
    cosDec = math.cos(math.asin(sinDec))

    # Stundenwinkel berechnen
    cosH = (math.cos(math.radians(zenith)) - (sinDec * math.sin(math.radians(latitude)))) / (cosDec * math.cos(math.radians(latitude)))

    # Prüfen, ob Sonnenaufgang oder -untergang möglich ist
    if cosH > 1 or cosH < -1:
        return None  # Kein Sonnenaufgang/-untergang

    # Stundenwinkel berechnen
    H = calculate_hour_angle(is_rise_time, cosH)

    # Lokale mittlere Zeit berechnen
    T = H + RA - (0.06571 * t) - 6.622
    UT = (T - lng_hour) % 24  # UTC-Zeit
    return UT

def calculate_sunrise_sunset(latitude, longitude, date, zenith=90.833):
    """Berechnet Sonnenaufgang und Sonnenuntergang in UTC."""
    # zenith = 90.833  # Ziviler Dämmerungswinkel
    sunrise_utc = calculate_sun_time(latitude, longitude, date, zenith, is_rise_time=False)
    sunset_utc = calculate_sun_time(latitude, longitude, date, zenith, is_rise_time=True)
    return sunrise_utc, sunset_utc


if __name__ == "__main__":
    latitude = 52.5200    # Breite von Berlin
    longitude = 13.4050   # Länge von Berlin
    date = (2025, 3, 20)  # Datum: 20. März 2025 (Tag- und Nachtgleiche)

    print(f"{'Zenitwinkel':<18} {'Sonnenaufgang':<18} {'Sonnenuntergang':<18} {'Zeitunterschied':<18}")
    for zenith in zenith_values:
        sunrise, sunset = calculate_sunrise_sunset(latitude, longitude, date, zenith=zenith)
        
        if sunrise is not None and sunset is not None:
            difference1 = time_difference_in_minutes(sunrise, sunset)
            print(f"{zenith:<18} {convert_dezimalzeit(sunrise):<18} {convert_dezimalzeit(sunset):<18} {difference1:<18}")
        else:
            print(f"Die Sonne geht an diesem Tag nicht auf oder unter.")

