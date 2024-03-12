# author = 'Christian Roepke'
# Program history: 
#  12.03.24  V. 1.0  Start 
# Functional description:
# Package to define state machine for Thread1

class Thread1_StateMachine:
    
    from standardize_coordinate_system import rotate_axes
    
    def __init__(self,Flags):
        self.Flags = Flags
    
    def StateMachine(self,sensData):
        #print('stateMachine Thread')
        if self.Flags.Flag_SensorData == 1:
            print('finish sensor data')
            self.Flags.Flag_SensorData = 0							# set 0 for receive new data
            sensData = Thread1_StateMachine.rotate_axes(sensData) 
            print('Acceleration rotated data:', sensData.acc)
            print('Gyro rotated data:', sensData.gyro)
            print('Magnetic rotated data:', sensData.mag)
            print('Temperature data:', sensData.temp)
#         elif self.Flags.Flag_SensorData == 0:
#             self.Flags.Flag_SensorData = 1
        if self.Flags.Flag_uart0_RX == 1:
            print('finish receive uart0 data')
            self.Flags.Flag_uart0_RX = 0							# set 0 for receive new data
#         elif self.Flags.Flag_uart0_RX == 0:
#             self.Flags.Flag_uart0_RX = 1