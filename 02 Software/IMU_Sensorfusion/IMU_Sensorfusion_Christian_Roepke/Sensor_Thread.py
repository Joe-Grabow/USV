# author = 'Christian Roepke'
# Program history: 
#  04.03.24  V. 1.0  Start
#  06.03.24  V. 1.1  Receive and read rotated data
#  12.03.24  V. 1.2  Global variables replaced and integration state machine in Thread1
# Functional description:
#  Package for receive and read rotated data from MPU9250 sensor

# load libaries
import time
import _thread
import ustruct
from machine import UART, Pin, I2C, Timer
from mpu9250 import MPU9250
from Flagclass import Flagclass
from MPU9250Data import MPU9250Data
from standardize_coordinate_system import rotate_axes
from Thread1_StateMachine import Thread1_StateMachine

print('thread 1 start')

# initialization UART0 and MPU9250 sensor
uart0 = UART(0, baudrate=250000, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)
uart0.flush()
uart0_rxData = bytes()

sensor = MPU9250(I2C(1, scl=Pin(7), sda=Pin(6), freq=400000))

sensData = MPU9250Data
Flags = Flagclass(0,0,1)

# define thread function (including thread 2 with collect and read data): 
def thread2(Flags, uart0, uart0_rxData):
    print('thread 2 start')
    def timT2_callback(timer):
        
        global sensor								# global variables cannot be transferred due to timer callback  
        global sensData
        global Flags
        #print('Timer callback')
        
        sensData.acc = sensor.acceleration			# functions from mpu9250.py file
        sensData.gyro = sensor.gyro
        sensData.mag = sensor.magnetic
        sensData.temp = sensor.temperature
        
        Flags.Flag_SensorData = 1;
    
    def uart0_RX_callback(uart0, uart0_rxData, Flags):
        if uart0.any() > 0:
            bf = uart0.read(1)
            if bf == b'\n':
                uart0_rxData += bf
                Flags.Flag_uart0_RX = 1
                print('read newline')
            else:
                uart0_rxData += bf
                
    timT2 = Timer()
    timT2.init(period=1000, callback=timT2_callback)
    
    try:
        while Flags.Flag_run_Thread2==1:
            uart0_RX_callback(uart0, uart0_rxData, Flags)
            
    finally:
        timT2.deinit()
    print('thread 2 end')     

# call and pass function from second core (Thread 2)
_thread.start_new_thread(thread2, (Flags, uart0, uart0_rxData,))

# Thread 1 (receive data):
try:
    led_onboard = Pin(25, Pin.OUT, value=1)
    state_machine = Thread1_StateMachine(Flags)
    
    while True:
        time.sleep(0.1)
        #print('stateMachine call')
        state_machine.StateMachine(sensData)

finally:
    Flags.Flag_run_Thread2 = 0
    led_onboard.off()
    time.sleep(0.1)
    print('thread 1 end')
