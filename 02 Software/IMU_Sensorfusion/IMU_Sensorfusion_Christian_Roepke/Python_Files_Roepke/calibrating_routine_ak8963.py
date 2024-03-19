# author = 'Christian Roepke'
# Program history: 
#  12.03.24  V. 1.0  Start
#  18.03.24  V. 1.1  including def check_cal_data() and the class calibration_routine_ak8963()
# Functional description:
#  Package for calibrate the magnet sensor AK8963

def save_cal_data(strFilename:str, c_data):
    import ujson
    with open(strFilename, 'w') as data:
        ujson.dump(c_data, data)
    
def load_cal_data(strFilename:str):
    with open(strFilename, 'r') as data:
        c_data = ujson.load(data)
    return(c_data)

def check_cal_data(strFilename:str):
    bIsfile = 0                               # flag for file exists
    try:
        file = open(strFilename, 'r')
        file.close()
        bIsfile = 1
    except:
        print('File not on System')
    return bIsfile

class calibration_routine_ak8963():
    
    import ujson
    
    def __init__(self):
        self.num_samples = 0
        self.bFinalCalibration = 0            # signal for cal finish
        self.x_min = 0
        self.x_max = 0
        self.y_min = 0
        self.y_max = 0
        self.z_min = 0
        self.z_max = 0
        self.xo = 0                           # zero point in x, y, z
        self.yo = 0
        self.zo = 0
        self.mag_x_values = []
        self.mag_y_values = []
        self.mag_z_values = []
        self.deltax = 0                       # width of the ellipse in the respective dimension
        self.deltay = 0
        self.deltaz = 0
        
    def cal(self,sensData):
        
        self.mag_x_values.append(sensData.mag[0])
        self.mag_y_values.append(sensData.mag[1])
        self.mag_z_values.append(sensData.mag[2])
              
        self.x_min = min(self.mag_x_values)
        self.x_max = max(self.mag_x_values)
        self.y_min = min(self.mag_y_values)
        self.y_max = max(self.mag_y_values)
        self.z_min = min(self.mag_z_values)
        self.z_max = max(self.mag_z_values)
        
        self.deltax = (self.x_max - self.x_min) 
        self.deltay = (self.y_max - self.y_min)
        self.deltaz = (self.z_max - self.z_min)
        
        self.xo = ((self.x_max - self.x_min) / 2) + self.x_min
        self.yo = ((self.y_max - self.y_min) / 2) + self.y_min
        self.zo = ((self.z_max - self.z_min) / 2) + self.z_min
        
#         if (self.mag_x_values[0] > 0 and self.mag_x_values[0 + 1] < 0):
#             print('Vorzeichenwechsel:', self.mag_x_values[0])
#         elif (self.mag_x_values[0] < 0 and self.mag_x_values[0 - 1] > 0):
#             print('Vorzeichenwechsel andere Richtung:', self.mag_x_values[i])
        
        print(self.xo)
        print(self.mag_y_values)
        print('------')
        # # Ausgabe der Kalibrierungswerte
        # print("X min:", self.x_min)
        # print("X max:", self.x_max)
        # print("Y min:", self.y_min)
        # print("Y max:", self.y_max)
        # print("Z min:", self.z_min)
        # print("Z max:", self.z_max)



