# author = 'Christian Roepke'
# Program history: 
#  06.03.24  V. 1.0  Start
#  06.03.24  V. 1.1  Tested and corrected
# Functional description:
#  Function for rotating the coordinate axes of the acceleration, gyro and magnet sensor into the ship's coordinate system

from MPU9250Data import MPU9250Data

def rotate_axes(data):
   
    data_t = MPU9250Data()
    data_t.acc = (-data.acc[2], data.acc[1], -data.acc[0])
    data_t.gyro = (data.gyro[2], -data.gyro[1], data.gyro[0])
    data_t.mag = (-data.mag[2], -data.mag[0], data.mag[1])
    
    return data_t

