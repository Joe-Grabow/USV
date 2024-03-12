# author = 'Christian Roepke'
# Program history: 
#  12.03.24  V. 1.0  Start 
# Functional description:
# Package to define for flag class Flag_SensorData, Flag_uart0_RX and Flag_run_Thread2

class Flagclass:
    
    def __init__(self, Flag_SensorData=0, Flag_uart0_RX=0, Flag_run_Thread2=0):
        self.Flag_SensorData = Flag_SensorData
        self.Flag_uart0_RX = Flag_uart0_RX
        self.Flag_run_Thread2 = Flag_run_Thread2