# load libary
import time
import _thread
import ustruct
from machine import UART, Pin, I2C, Timer
from mpu9250 import MPU9250

# define MPU9250 data class for time, accleration, gyro, magnetic and temperature data
class MPU9250Data:
    time: 0
    acc:  1
    gyro: 2
    mag:  3
    temp: 4
    
print('thread 1 start')

# initialization UART0 and MPU9250 sensor
uart0 = UART(0, baudrate=250000, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)
uart0.flush()
uart0_rxData = bytes()

sensor = MPU9250(I2C(1, scl=Pin(7), sda=Pin(6), freq=400000))

sensData = MPU9250Data
Flag_SensorData = 0
Flag_uart0_RX = 0
Flag_run_Thread2 = 1

# define thread function (including thread 2 with collect and read data): 
def UART0Rx():
    print('thread 2 start')
    
    def timT2_callback(timer):
        
        global sensor
        global sensData
        global Flag_SensorData
        global Flag_run_Thread2
        print('Timer callback')
        
        sensData.acc = sensor.acceleration			#functions from mpu9250.py file
        sensData.gyro = sensor.gyro
        sensData.mag = sensor.magnetic
        sensData.temp = sensor.temperature
        
        Flag_SensorData = 1;
    
    def uart0_RX_callback():
        
        global uart0
        global uart0_rxData
        global Flag_uart0_RX
       
        if uart0.any() > 0:
            bf = uart0.read(1)
            if bf == b'\n':
                uart0_rxData += bf
                Flag_uart0_RX = 1
                print('read newline')
            else:
                uart0_rxData += bf
                
    timT2 = Timer()
    timT2.init(period=1000, callback=timT2_callback)
    
    while Flag_run_Thread2==1:
        uart0_RX_callback()
        
    timT2.deinit()
    print('thread 2 end')     

# call and pass function
_thread.start_new_thread(UART0Rx, ())

# test: 
#txData = b'hello world\n'
#uart0.write(txData)

# Thread 1 (receive data):
while True:
    if Flag_SensorData == 1:
        print('finish sensor data')
        Flag_SensorData = 0								# set 0 for receive new data 
        print('Acceleration data:', sensData.acc)
        print('Gyro data:', sensData.gyro)
        print('Magnetic data:', sensData.mag)
        print('Temperature data:', sensData.temp)
    if Flag_uart0_RX == 1:
        print('finish receive uart0 data')
        Flag_uart0_RX = 0								# set 0 for receive new data
        
Flag_run_Thread2 = 0
time.sleep(0.1)
print('thread 1 end')