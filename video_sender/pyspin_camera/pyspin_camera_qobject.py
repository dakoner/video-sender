import signal
import sys
import numpy as np
import pdb
from PyQt5 import QtCore
import PySpin

LOGGING_LEVEL = PySpin.LOG_LEVEL_WARN

class LoggingEventHandler(PySpin.LoggingEventHandler):

    def __init__(self):
        super(LoggingEventHandler, self).__init__()

    def OnLogEvent(self, logging_event_data):
        print('Category: %s' % logging_event_data.GetCategoryName())
        print('Priority Value: %s' % logging_event_data.GetPriority())
        print('Priority Name: %s' % logging_event_data.GetPriorityName())
        print('Timestamp: %s' % logging_event_data.GetTimestamp())
        print('NDC: %s' % logging_event_data.GetNDC())
        print('Thread: %s' % logging_event_data.GetThreadName())
        print('Message: %s' % logging_event_data.GetLogMessage())
        print()

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
            pass
            #print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
        else:
            print(image_result.GetTimeStamp())
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
    bufferHandlingModeChanged = QtCore.pyqtSignal(bool)
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)
    def __init__(self):
        super().__init__()
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.camera = self.cam_list[0]
        self.logging_event_handler = LoggingEventHandler()
        self.system.RegisterLoggingEventHandler(self.logging_event_handler)
        self.system.SetLoggingEventPriorityLevel(LOGGING_LEVEL)
        self.init()

    def init(self):
        self.camera.Init()
        self.nodemap_tldevice = self.camera.GetTLDeviceNodeMap()
        self.nodemap = self.camera.GetNodeMap()
        self.nodemap_stream = self.camera.GetTLStreamNodeMap()
        self.acquisitionMode = 'SingleFrame'
        self.autoExposureMode = True
        self.bufferHandlingMode = 'NewestOnly'

        self.worker = None
       

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
        acquisitionMode_entry = node_acquisition_mode.GetEntryByName(acquisitionMode)
        if acquisitionMode_entry == None:
            print("Invalid acquisition mode", acquisitionMode)
            return
        acquisitionMode_value = acquisitionMode_entry.GetValue()
        if acquisitionMode_value == node_acquisition_mode.GetIntValue():
                return
        node_acquisition_mode.SetIntValue(acquisitionMode_value)
        self.acquisitionModeChanged.emit(node_acquisition_mode.GetIntValue()) 

    @QtCore.pyqtProperty(str, notify=bufferHandlingModeChanged)
    def bufferHandlingMode(self):
        return self.camera.bufferHandlingMode.ToString()

    @bufferHandlingMode.setter
    def bufferHandlingMode(self, bufferHandlingMode):
        node_streamBufferHandlingMode = PySpin.CEnumerationPtr(self.nodemap_stream.GetNode('StreamBufferHandlingMode'))
        print(node_streamBufferHandlingMode)
        bufferHandlingMode_entry = node_streamBufferHandlingMode.GetEntryByName(bufferHandlingMode)
        if bufferHandlingMode_entry == None:
            print("Invalid buffer handling mode", bufferHandlingMode)
            return
        bufferHandlingMode_value = bufferHandlingMode_entry.GetValue()
        if bufferHandlingMode_value == node_streamBufferHandlingMode.GetIntValue():
            return
        node_streamBufferHandlingMode.SetIntValue(bufferHandlingMode_value)
        self.bufferHandlingModeChanged.emit(node_streamBufferHandlingMode.GetIntValue()) 



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
        
