# author = 'Christian Roepke'
# Program history: 
#  06.03.24  V. 1.0  Start
#  11.03.24  V. 1.1  
# Functional description:
# Package to define MPU9250 data class for time, accleration, gyro, magnetic and temperature data

class MPU9250Data:

    def sensData(self, time=0, acc=(0,0,0), gyro=(0,0,0), mag=(0,0,0), temp=0):
        self.time = time
        self.acc = acc
        self.gyro = gyro
        self.mag = mag
        self.temp = temp