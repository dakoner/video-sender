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
    ExposureAutoChanged = QtCore.pyqtSignal(bool)
    ExposureModeChanged = QtCore.pyqtSignal(bool)
    acquisitionModeChanged = QtCore.pyqtSignal(bool)
    triggerModeChanged = QtCore.pyqtSignal(bool)
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
        self.acquisitionMode = 'Continuous'
        self.ExposureAuto = 'Off'
        self.ExposureMode = 'Timed'
        self.triggerMode = 'Off'
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


    @QtCore.pyqtProperty(str, notify=triggerModeChanged)
    def triggerMode(self):
        return self.camera.triggerMode.ToString()

    @triggerMode.setter
    def triggerMode(self, triggerMode):
        node_trigger_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('TriggerMode'))
        triggerMode_entry = node_trigger_mode.GetEntryByName(triggerMode)
        if triggerMode_entry == None:
            print("Invalid trigger mode", triggerMode)
            return
        triggerMode_value = triggerMode_entry.GetValue()
        if triggerMode_value == node_trigger_mode.GetIntValue():
                return
        node_trigger_mode.SetIntValue(triggerMode_value)
        self.triggerModeChanged.emit(node_trigger_mode.GetIntValue()) 

    @QtCore.pyqtProperty(str, notify=bufferHandlingModeChanged)
    def bufferHandlingMode(self):
        return self.camera.bufferHandlingMode.ToString()

    @bufferHandlingMode.setter
    def bufferHandlingMode(self, bufferHandlingMode):
        node_streamBufferHandlingMode = PySpin.CEnumerationPtr(self.nodemap_stream.GetNode('StreamBufferHandlingMode'))
        bufferHandlingMode_entry = node_streamBufferHandlingMode.GetEntryByName(bufferHandlingMode)
        if bufferHandlingMode_entry == None:
            print("Invalid buffer handling mode", bufferHandlingMode)
            return
        bufferHandlingMode_value = bufferHandlingMode_entry.GetValue()
        if bufferHandlingMode_value == node_streamBufferHandlingMode.GetIntValue():
            return
        node_streamBufferHandlingMode.SetIntValue(bufferHandlingMode_value)
        self.bufferHandlingModeChanged.emit(node_streamBufferHandlingMode.GetIntValue()) 


    @QtCore.pyqtProperty(str, notify=ExposureAutoChanged)
    def ExposureAuto(self):
        return self.camera.ExposureAuto.ToString()

    @ExposureAuto.setter
    def ExposureAuto(self, ExposureAuto):
        node_ExposureAuto = PySpin.CEnumerationPtr(self.nodemap.GetNode('ExposureAuto'))
        ExposureAuto_entry = node_ExposureAuto.GetEntryByName(ExposureAuto)
        if ExposureAuto_entry == None:
            print("Invalid auto exposure mode", ExposureAuto)
            return
        ExposureAuto_value = ExposureAuto_entry.GetValue()
        if ExposureAuto_value == node_ExposureAuto.GetIntValue():
            return
        node_ExposureAuto.SetIntValue(ExposureAuto_value)
        self.ExposureAutoChanged.emit(node_autoExposureMode.GetIntValue()) 




    @QtCore.pyqtProperty(str, notify=ExposureModeChanged)
    def ExposureMode(self):
        return self.camera.ExposureMode.ToString()

    @ExposureMode.setter
    def ExposureMode(self, ExposureMode):
        node_ExposureMode = PySpin.CEnumerationPtr(self.nodemap.GetNode('ExposureMode'))
        ExposureMode_entry = node_ExposureMode.GetEntryByName(ExposureMode)
        if ExposureMode_entry == None:
            print("Invalid exposure mode", ExposureMode)
            return
        ExposureMode_value = ExposureMode_entry.GetValue()
        if ExposureMode_value == node_ExposureMode.GetIntValue():
            return
        node_ExposureMode.SetIntValue(ExposureMode_value)
        self.ExposureModeChanged.emit(node_autoExposureMode.GetIntValue()) 

    @QtCore.pyqtProperty(float, notify=exposureChanged)
    def exposure(self):
        return self.camera.ExposureTime.GetValue()

    @exposure.setter
    def exposure(self, exposure):
        print("Autoexposure value:",  self.camera.ExposureTime.GetValue())
        if exposure == self.camera.ExposureTime.GetValue():
            return
        self.camera.ExposureTime.SetValue(exposure)
        self.exposureChanged.emit(self.camera.ExposureTime.GetValue()) 
        
