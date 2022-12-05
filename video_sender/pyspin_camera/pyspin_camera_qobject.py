import signal
import sys
import numpy as np
import pdb
from PyQt5 import QtCore
import PySpin



class Worker(QtCore.QThread):
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)

    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        
        
    @QtCore.pyqtSlot()
    def run(self):
        while True:
            self.acquire_callback()
        

    def acquire_callback(self):
        image_result = self.camera.GetNextImage()
        if image_result.IsIncomplete():
            print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
        else:
            width = image_result.GetWidth()
            height = image_result.GetHeight()
            stride = image_result.GetStride()
            d = image_result.GetData()
            d= d.reshape((height,width,1))
            
            self.imageChanged.emit(d, width, height, stride)


class PySpinCamera(QtCore.QObject):
    exposureChanged = QtCore.pyqtSignal(float)
    autoExposureModeChanged = QtCore.pyqtSignal(bool)
    acquisitionModeChanged = QtCore.pyqtSignal(bool)
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)

    def __init__(self):
        super().__init__()
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.camera = self.cam_list[0]
        self.camera.Init()
        self.camera.acquisitionMode = 'Continuous'
        self.camera.autoExposureMode = True

        self.worker = None
       
        self.nodemap_tldevice = self.camera.GetTLDeviceNodeMap()
        self.camera.Init()
        self.nodemap = self.camera.GetNodeMap()

    def callback(self, d, w, h, s):
        self.imageChanged.emit(d, w, h, s)

    def begin(self):
        self.worker = Worker(self.camera)
        self.worker.imageChanged.connect(self.callback, QtCore.Qt.DirectConnection)
        self.worker.start()
        self.camera.BeginAcquisition()

    def end(self):
        self.worker.terminate()
        self.worker = None
        self.camera.EndAcquisition()

    @QtCore.pyqtProperty(str, notify=acquisitionModeChanged)
    def acquisitionMode(self):
        return self.camera.AcquisitionMode.ToString()

    @acquisitionMode.setter
    def acquisitionMode(self, acquisitionMode):
        node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionMode'))
        acquisitionMode_value = node_acquisition_mode.GetEntryByName(acquisitionMode).GetValue()
        if acquisitionMode_value == node_acquisition_mode.GetIntValue(): return
        node_acquisition_mode.SetIntValue(acquisitionMode_value)
        self.acquisitionModeChanged.emit(node_acquisition_mode.GetIntValue()) 



    @QtCore.pyqtProperty(bool)#, notify=autoExposureModeChanged)
    def autoExposureMode(self):
        try:
            node_autoExposure_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('ExposureAuto'))    
            currentValue = node_autoExposure_mode.GetIntValue()
            if currentValue == PySpin.ExposureAuto_Off: returnValue= False
            elif currentValue == PySpin.ExposureAuto_Continuous: returnValue= True
            return returnValue
        except:
            import traceback
            traceback.print_exc()

    @autoExposureMode.setter
    def autoExposureMode(self, autoExposureMode):
        currentValue = self.camera.ExposureAuto.GetValue()
        if autoExposureMode is False:
            if currentValue is PySpin.ExposureAuto_Off: return
            self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

        elif autoExposureMode is True:
            if currentValue is PySpin.ExposureAuto_Continuous: return
            self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)

        currentValue = self.camera.ExposureAuto.GetValue()

        if currentValue == PySpin.ExposureAuto_Off: returnValue= False
        elif currentValue == PySpin.ExposureAuto_Continuous: returnValue= True
        self.autoExposureModeChanged.emit(returnValue) 

    @QtCore.pyqtProperty(float, notify=exposureChanged)
    def exposure(self):
        return self.camera.ExposureTime.GetValue()

    @exposure.setter
    def exposure(self, exposure):
        print("Autoexposure value:",  self.camera.ExposureAuto.GetValue())
        if exposure == self.camera.ExposureTime.GetValue():
            return
        self.camera.ExposureTime.SetValue(exposure)
        self.exposureChanged.emit(self.camera.ExposureTime.GetValue()) 
        
