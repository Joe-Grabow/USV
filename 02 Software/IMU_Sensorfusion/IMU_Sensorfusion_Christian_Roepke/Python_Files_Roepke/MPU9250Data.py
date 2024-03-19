# author = 'Christian Roepke'
# Program history: 
#  06.03.24  V. 1.0  Start
#  11.03.24  V. 1.1  including def __init__()
#  18.03.24  V. 1.2  including def copy()
# Functional description:
# Package to define MPU9250 data class for time, accleration, gyro, magnetic and temperature data
# and copy the MPU9250 data

class MPU9250Data:
    
    def __init__(self, time=0, acc=(0,0,0), gyro=(0,0,0), mag=(0,0,0), temp=0):
        self.time = time
        self.acc = acc
        self.gyro = gyro
        self.mag = mag
        self.temp = temp
        
    def copy(self):
        c = MPU9250Data(time = self.time, acc = self.acc, gyro = self.gyro, mag = self.mag, temp = self.temp)
        return c