# -*- coding: utf-8 -*-
"""
Created on Wed Nov 29 08:24:08 2023

@author: Grabow
"""
__version__ = '1.0'
__author__ = 'Joe Grabow'


def drive_night(trigger):
    global output_set
    match trigger:
        case {"W1": True, "W2": True}:
            print('LED W1 OFF')
            print('LED W2 OFF')
            print('Error W')
        
        case {"W1": True, "W2": False}:
            print('LED W2 full')
            print('Fail W')
 
        case {"W2": True, "W1": False}:
            print('LED W1 full')
            print('Fail W')       
 
        case {"RG": True}:
            print('LED RG OFF')
            print('Fail RG')      
    
        case _:
            print('LED W1 half')
            print('LED W2 half')    
            print('LED RG ON')       
    return


def anchor_night(trigger):
    match trigger:
        case {"W1": True, "W2": True}:
            print('LED W1 OFF')
            print('LED W2 OFF')
            print('Error W')
        
        case {"W1": True, "W2": False}:
            print('LED W2 full')
            print('Fail W')
 
        case {"W2": True, "W1": False}:
            print('LED W1 full')
            print('Fail W')       
 
        case {"RG": True}:
            print('LED RG OFF')
            print('Fail RG')      
    
        case _:
            print('LED W1 half')
            print('LED W2 half')    
            print('LED RG OFF')       
    return


# all User-State-Functions
def s_f_1(trigger):  # Zustand 1
    global output_set
    if trigger["Bus"]:
        print('\n','Busfehler')
        drive_night(trigger)
    else:    
        print('\n','Fahrt Tag')
        print('LED W1 OFF')
        print('LED W2 OFF')
        print('LED RG OFF')

    return

def s_f_2(trigger):  # Zustand 2
    if trigger["Bus"]:
        print('\n','Busfehler')
        drive_night(trigger)
    else: 
        print('\n','Fahrt Nacht')
        drive_night(trigger)
    return

def s_f_3(trigger):  # Zustand 3
    if trigger["Bus"]:
        print('\n','Busfehler')
        drive_night(trigger)
    else: 
        print('\n','Anker Tag')
        print('LED W1 OFF')
        print('LED W2 OFF')
    return

def s_f_4(trigger):  # Zustand 4
    if trigger["Bus"]:
        print('\n','Busfehler')
        drive_night(trigger)
    else: 
        print('\n','Anker Nacht')
        anchor_night(trigger)
    return

