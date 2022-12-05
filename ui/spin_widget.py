import time
from PyQt5 import QtGui, QtCore, QtWidgets
from pyspin_camera_qobject import PySpinCamera
import PySpin

import numpy as np

class SpinWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(SpinWidget, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel()
        self.layout.addWidget(self.label)
        self.label.setFixedSize(1440,1080)


        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.cam = self.cam_list[0]
        print(self.cam_list)
        import pdb; pdb.set_trace()
        self.camera = PySpinCamera(self.cam)

        self.camera.imageChanged.connect(self.camera_callback)
        
        self.camera.initialize()
        self.camera.acquisitionMode = 'Continuous'
        self.camera.autoExposureMode = True
        #self.camera.exposure=5.0

        self.camera.begin()
    
        self.sp = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sp.valueChanged.connect(self.exposure_change)
        self.sp.setMinimum(0)
        self.sp.setMaximum(100000)
        self.sp.setValue(0)
        self.sp.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.sp.setTickInterval(5000)
        self.layout.addWidget(self.sp)


        self.gp = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gp.valueChanged.connect(self.gain_change)
        self.gp.setMinimum(0)
        self.gp.setMaximum(48)
        self.gp.setValue(0)
        self.gp.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.gp.setTickInterval(5)
        self.layout.addWidget(self.gp)

    def exposure_change(self, value):
        if value == 0:
            print("enable auto")
            self.camera.autoExposureMode = True
        else:
            print('set exposure time to', value)
            self.camera.autoExposureMode = False
            self.camera.exposure = value
        return True


    def gain_change(self, value):
        if value == 0:
            print("enable auto")
        else:
            print('set exposure time to', value)
            self.camera.configure_gain(value)
        return True

    def camera_callback(self, d, width, height, stride):
        t0 = time.time()
        #print(t0-self.t0)
        self.t0 = t0
        image = QtGui.QImage(d, width, height, stride, QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)





# class QApplication(QtCore.QCoreApplication):
#     def __init__(self, *args, **kwargs):
#         super(QApplication, self).__init__(*args, **kwargs)
            
#         self.system = PySpin.System.GetInstance()
#         self.cam_list = self.system.GetCameras()
#         self.cam = self.cam_list[0]
#         self.p = PySpinCamera(self.cam)

#         self.p.imageChanged.connect(self.acq_callback)
#         self.p.exposureChanged.connect(self.exp_callback)


#         self.p.initialize()
#         self.p.acquisitionMode = 'Continuous'
#         self.p.autoExposureMode = False
#         self.p.exposure=5.0

#         self.p.begin()
    

#         self.time.timeout.connect(self.changeExposure)
#         self.time.start(1000)

#     def changeExposure(self): 
#         print("set exposure to 5")       
#         self.p.exposure=5.0

#     def exp_callback(self, value):
#         print("exposure", value)


#     def __del__(self):
#         self.cam.DeInit()
#         del self.p
#         del self.cam
#         self.cam_list.Clear()
#         self.system.ReleaseInstance()

# if __name__ == "__main__":
#     signal.signal(signal.SIGINT, signal.SIG_DFL)

#     q = QApplication(sys.argv)
#     q.exec_()
    

#     # p.begin()
#     # while True:
#     #     print(p.acquire())