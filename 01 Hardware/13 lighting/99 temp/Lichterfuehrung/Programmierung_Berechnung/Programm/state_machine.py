# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 12:00:12 2025

@author: Joe Grabow (grabow@amesys.de)


The state machine changes its state depending on the input. 
If no input matches, it does not change its state.
"""
__version__ = '1.0'
__author__ = 'Joe Grabow'

class StateMachine:
    def __init__(self):
        self.state = 1  # default state to start
        
        
    # in_state  : current state
    # input_sw  : 1=drive, 2=anchor, 3=sunset, 4=sunrise, 5=light, 6=dark
    def transition(self, in_state, trigger):
        if (in_state == 1 and trigger["sunset"]) or (in_state == 1 and trigger["dark"]):  # go state 2
            self.state = 2                              # Nachtfahrt
            
        elif (in_state == 2 and trigger["sunrise"]) or (in_state == 2 and trigger["light"]):  # go state 1
            self.state =1                               # Tagfahrt
            
        elif in_state == 1 and trigger["anchor"]:       # go state 3
            self.state = 3                              # Anker Tag
            
        elif in_state == 3 and trigger["drive"]:        # go state 1
            self.state = 1                              # Tagfahrt
            
        elif in_state == 2 and trigger["anchor"]:       # go state 4
            self.state = 4                              # Anker Nacht
            
        elif in_state == 4 and trigger["drive"]:        # go state 2
            self.state = 2                              # Nachtfahrt
            
        elif (in_state == 4 and trigger["sunrise"]) or (in_state == 4 and trigger["light"]):  # go state 3
            self.state = 3                              # Anker Tag
            
        elif (in_state == 3 and trigger["sunset"]) or (in_state == 3 and trigger["dark"]):  # go state 4
            self.state = 4                              # Anker Nacht
            
        else:
            self.state = self.state                     # old state = new state
        return self.state