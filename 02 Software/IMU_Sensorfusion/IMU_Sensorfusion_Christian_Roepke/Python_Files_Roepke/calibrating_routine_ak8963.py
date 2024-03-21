# author = 'Christian Roepke'
# Program history: 
#  12.03.24  V. 1.0  Start
#  18.03.24  V. 1.1  including def check_cal_data() and the class calibration_routine_ak8963()
#  20.03.24  V. 1.2  including def findPerAndCalc(), def cal() and def valueCorrect()
# Functional description:
#  Package for calibrate the magnet sensor AK8963
    
class calibration_routine_ak8963():
    
    import ujson
    
    def __init__(self):
        self.strFilename = 'cal_data.json'
        self.num_samples = 0
        self.bFinalCalibration = 0             # signal for calibration is finish
        
        self.data = {"x_min": 0,
                "x_max": 0,
                "y_min" : 0,
                "y_max" : 0,
                "z_min" : 0,
                "z_max" : 0,
                "xo" : 0,                      # zero point in x, y, z
                "yo" : 0,
                "zo" : 0,
                "deltax" : 0,                  # width of the ellipse in the respective dimension
                "deltay" : 0,
                "deltaz" : 0,
                "scale_x": 1,
                "scale_y": 1,
                "scale_z": 1,
                }
  
        self.mag_x_values = []
        self.mag_y_values = []
        self.mag_z_values = []
    
    def check_cal_data(self):
        bIsfile = 0                               # flag for file exists
        try:
            file = open(self.strFilename, 'r')
            file.close()
            bIsfile = 1
        except:
            print('File not on System')
        return bIsfile
    
    def load_cal_data(self):
        import ujson
        with open(self.strFilename, 'r') as data:
            self.data = ujson.load(data)
           
    def save_cal_data(self):
        import ujson
        with open(self.strFilename, 'w') as data:
            ujson.dump(self.data, data)
        
    def findPerAndCalc(self, mag_values):
        
        zero_cross = []
        isFindZeros = 0
        mag_values_per = []
        r = [0,0,0,0,0]
        
        for i in range(len(mag_values)-1):
            if mag_values[i] > 0 and mag_values[i+1] < 0:
                zero_cross.append(i)
            elif mag_values[i] < 0 and mag_values[i+1] > 0:
                zero_cross.append(i)
        
        if len(zero_cross) >= 4:
            isFindZeros = 1                 # check for full Period
            for i in range(zero_cross[-3], zero_cross[-1]+1):
                mag_values_per.append(mag_values[i])
            print('..............')
            #print(mag_values_per)
            #print('....')
            #print(zero_cross[-3])
            #print(zero_cross[-1])
            #print('....')
            v_min = min(mag_values_per)
            v_max = max(mag_values_per)
            v_delta = (v_max - v_min)
            vo = (v_delta / 2) + v_min
           
            #print(v_min)
            #print(v_max)
            #print(v_delta)
            #print(vo)
            #print('..............')
            r = [v_min, v_max, v_delta, vo, isFindZeros]
            print(r)
            
        return r
    
    def cal(self,sensData):
        
        self.mag_x_values.append(sensData.mag[0])
        self.mag_y_values.append(sensData.mag[1])
        self.mag_z_values.append(sensData.mag[2])
        
        isFindZeros = [0,0,0]                 # indicates whether period is complete
        
        vec_V = self.findPerAndCalc(self.mag_x_values)
        print(vec_V)
        self.data["x_min"] = vec_V[0]
        self.data["x_max"] = vec_V[1]
        self.data["deltax"] = vec_V[2]
        self.data["xo"] = vec_V[3]
        isFindZeros[0] = vec_V[4]
        
        vec_V = self.findPerAndCalc(self.mag_y_values)
        self.data["y_min"] = vec_V[0]
        self.data["y_max"] = vec_V[1]
        self.data["deltay"] = vec_V[2]
        self.data["yo"] = vec_V[3]
        isFindZeros[1] = vec_V[4]
        
        vec_V = self.findPerAndCalc(self.mag_z_values)
        self.data["z_min"] = vec_V[0]
        self.data["z_max"] = vec_V[1]
        self.data["deltaz"] = vec_V[2]
        self.data["zo"] = vec_V[3]
        isFindZeros[2] = vec_V[4]
          
        print('isFindZeros')
        print(isFindZeros)
        print('------')
        
        if all(isFindZeros):
            
            self.bFinalCalibration = 1
            
            avg_delta_x = (self.data["x_max"] - self.data["x_min"]) / 2
            avg_delta_y = (self.data["y_max"] - self.data["y_min"]) / 2
            avg_delta_z = (self.data["z_max"] - self.data["z_min"]) / 2
            
            avg_delta = (avg_delta_x + avg_delta_y + avg_delta_z) / 3
            
            self.data["scale_x"] = avg_delta / avg_delta_x
            self.data["scale_y"] = avg_delta / avg_delta_y
            self.data["scale_z"] = avg_delta / avg_delta_z
            
    def valueCorrect(self, tuple_xyz):
        
        tuple_xyz = list(tuple_xyz)
        
        # Apply hard iron ie. offset bias from calibration
        tuple_xyz[0] -= self.data["xo"]
        tuple_xyz[1] -= self.data["yo"]
        tuple_xyz[2] -= self.data["zo"]

        # Apply soft iron ie. scale bias from calibration
        tuple_xyz[0] *= self.data["scale_x"]
        tuple_xyz[1] *= self.data["scale_y"]
        tuple_xyz[2] *= self.data["scale_z"]

        return tuple(tuple_xyz)




