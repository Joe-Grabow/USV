# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 11:29:47 2024
@author: Grabow


Das Tool den Datenblock aus einer CSV-Datei und speichert ihn in einem 
Dictionary bestehent aus dem Key und einem Tupel [Adresse dezimal, Adresse hex] 
Dieses Dictionary wird in der Datei "datablock.json" abgespeichert und kann
für weitere Programme wieder importiert werden. 


Program history
17.01.2024    V. 1.0    Start

@author: Prof. Jörg Grabow (grabow@amesys.de)
"""

__version__ = '1.0'
__author__ = 'Joe Grabow'

import csv
import json


def read_csv_to_dict(file_path):
    data_dict = {}

    with open(file_path, 'r', encoding="latin-1", newline='') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=';')
        
        # Überspringe die erste Zeile
        next(csv_reader, None)
        
        # Annahme: Die Datei hat mindestens 4 Spalten
        for row in csv_reader:
            if len(row) >= 4:
                key = row[2]  # dritte Spalte als Key
                decimal_value = int(row[0], 16)  # erste Spalte (Adresse dezimal)
                hex_value = hex(decimal_value)  # erste Spalte (Adresse hexadezimal)
                address = int(row[1], 10)
                data_dict[key] = hex_value, decimal_value, address
    return data_dict

json_file = 'datablock.json'
csv_file = 'Datenblock.csv'  

datablock = read_csv_to_dict(csv_file)  # read CSV Data and convert 

with open(json_file, 'w') as json_data:
    json.dump(datablock, json_data)
    

"""    
# read JSON-Data
with open(json_file, 'r') as json_data:
    datablock = json.load(json_data)

print(f'Datenblock: {datablock}')
"""