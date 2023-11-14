# coding: utf-8
"""
Program history
08.11.2023    V. 1.0    Start
10.11.2023    V. 1.1    Calibration Data for the Magnetic Sensor

IMU measuring demo system for USV project
A calibration file "cal_data.json" is required.
The measured values of acceleration, gyroscope, magnetometer, and temperature are captured and output.
When the "j_flag" is set, magnetometer data is immediately compensated with calibration data during the
measurement.

https://github.com/Joe-Grabow/USV

@author: Joe Grabow (grabow@amesys.de)
"""
__version__ = '1.1'
__author__ = 'Joe Grabow'

import ujson
import utime
from machine import I2C, Pin
from mpu9250 import MPU9250
from ak8963 import AK8963

# load calibrate Data
def load_cal_data():
    with open('cal_data.json', 'r') as data:
        c_data = ujson.load(data)
    return(c_data)

# I2C port on Measurement-Board
i2c = I2C(1,scl=Pin(7),sda=Pin(6),freq=400_000)

# cal_data.json
# j_flag   0  sensor uncalibrated
#          1  sensor calibrated
# j_offset [x, y, z]
# j_scale  [x, y, z]
[j_flag, j_offset, j_scale] = load_cal_data()

if j_flag == 0:  # uncalibrated
    j_offset = [0 for _ in j_offset]  # all 0
    j_scale = [1 for _ in j_scale]  # all 1
else:  # use the calibrated data
    pass

print(j_offset, j_scale)
dummy = MPU9250(i2c) # this opens the bybass to access to the AK8963

ak8963 = AK8963(
    i2c,
    offset=(j_offset[0], j_offset[1], j_offset[2]),
    scale=(j_scale[0], j_scale[2], j_scale[2])
)

sensor = MPU9250(i2c, ak8963=ak8963)

print("MPU9250 id: " + hex(sensor.whoami))


while True:
    print(sensor.acceleration)
    print(sensor.gyro)
    print(sensor.magnetic)
    print(sensor.temperature)
    
    utime.sleep_ms(1000)