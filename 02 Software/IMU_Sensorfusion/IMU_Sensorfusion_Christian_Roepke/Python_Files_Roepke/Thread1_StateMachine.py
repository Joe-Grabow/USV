# author = 'Christian Roepke'
# Program history: 
#  12.03.24  V. 1.0  Start
#  18.03.24  V. 1.1  define the state Machine as a class, including def __init__, extension of the state machine
#  20.03.24  V. 1.2  extension of the state Machine
# Functional description:
# Package to define the state machine for IMU

class Thread1_StateMachine:
    
    from standardize_coordinate_system import rotate_axes
    from calibrating_routine_ak8963 import calibration_routine_ak8963
        
    def __init__(self,Flags):
        self.Flags = Flags
        self.state = 0     												# 0 for init
        self.Calibrate = Thread1_StateMachine.calibration_routine_ak8963()
        self.sensData = []
    
    def StateMachine(self,sensData):
        #print('stateMachine Thread')
#         if self.Flags.Flag_SensorData == 1:
#             print('finish sensor data')
#             self.Flags.Flag_SensorData = 0							# set 0 for receive new data
#             sensData = Thread1_StateMachine.rotate_axes(sensData) 
#             print('Acceleration rotated data:', sensData.acc)
#             print('Gyro rotated data:', sensData.gyro)
#             print('Magnetic rotated data:', sensData.mag)
#             print('Temperature data:', sensData.temp)
#         elif self.Flags.Flag_SensorData == 0:
#             self.Flags.Flag_SensorData = 1
        if self.Flags.Flag_uart0_RX == 1:
            print('finish receive uart0 data')
            self.Flags.Flag_uart0_RX = 0							# set 0 for receive new data
#         elif self.Flags.Flag_uart0_RX == 0:
#             self.Flags.Flag_uart0_RX = 1

#         print('state')
#         print(self.state)
        
        if self.state == 0:
            self.state = 1
        elif self.state == 1:
            # debug to state 8
            #self.state = 8
            if self.Calibrate.check_cal_data():
                self.Calibrate.load_cal_data()
                print('read cal_data.json')
                self.state = 2
            else:
#                 self.state = 3
                # debug to state 8
                self.state = 8
        elif self.state == 2:
            if self.Flags.Flag_SensorData == 1:
                self.state = 4
        elif self.state == 3:
            if self.Flags.Flag_SensorData == 1:
                self.state = 6
        elif self.state == 4:
            print('state 4')
            self.sensData = sensData.copy()
            self.sensData = Thread1_StateMachine.rotate_axes(self.sensData)
            self.state = 5
        elif self.state == 5:
            print('state 5')
            self.sensData.mag = self.Calibrate.valueCorrect(self.sensData.mag)
            print(self.sensData.mag)
            self.state = 2
        elif self.state == 6:
            self.sensData = sensData.copy()
            self.Flags.Flag_SensorData = 0							# set 0 for receive new data
            self.sensData = Thread1_StateMachine.rotate_axes(self.sensData)
            self.state = 7
        elif self.state == 7:
            #print('Acceleration rotated data:', self.sensData.acc)
            #print('Gyro rotated data:', self.sensData.gyro)
            print('Magnetic rotated data:', self.sensData.mag)
            #print('Temperature data:', self.sensData.temp)
            self.state = 3
        elif self.state == 8:
            if self.Calibrate.bFinalCalibration == 1:
                self.state = 11
            elif self.Flags.Flag_SensorData == 1:
                self.sensData = sensData.copy()
                self.Flags.Flag_SensorData = 0
                self.state = 9
        elif self.state == 9:
            self.sensData = Thread1_StateMachine.rotate_axes(self.sensData)
            self.state = 10
        elif self.state == 10:
            self.Flags.Flag_SensorData = 0
            self.Calibrate.cal(self.sensData)
            self.state = 8
        elif self.state == 11:
            self.Calibrate.save_cal_data()
            self.state = 2