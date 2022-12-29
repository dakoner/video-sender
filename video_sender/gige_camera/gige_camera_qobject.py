import signal
import sys
import numpy as np
import pdb
from PyQt5 import QtCore
import mvsdk


class GigECamera(QtCore.QObject):
    imageChanged = QtCore.pyqtSignal(np.ndarray)
    ExposureTimeChanged = QtCore.pyqtSignal(float)
    TriggerModeChanged = QtCore.pyqtSignal(float)
    HMirrorChanged = QtCore.pyqtSignal(float)
    VMirrorChanged = QtCore.pyqtSignal(float)
    AeStateChanged = QtCore.pyqtSignal(float)
    AeTargetChanged = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        if nDev < 1:
            print("No camera was found!")
            return
            
        for i, DevInfo in enumerate(DevList):
            print("{}: {} {}".format(i, DevInfo.GetFriendlyName(), DevInfo.GetPortType()))
        i = 0 if nDev == 1 else int(input("Select camera: "))
        DevInfo = DevList[i]

        
        self.hCamera = 0
        try:
            self.hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
            return


    @QtCore.pyqtProperty(int, notify=VMirrorChanged)
    def VMirror(self):
        return mvsdk.CameraGetMirror(self.hCamera, 1)

    @VMirror.setter
    def VMirror(self, mode):
        print('current mode:', mvsdk.CameraGetMirror(self.hCamera, 1))
        print('set mode to', mode)
        if mode == mvsdk.CameraGetMirror(self.hCamera, 1):
            return
        print("Result: ", mvsdk.CameraSetMirror(self.hCamera, 1, mode))
        self.VMirrorChanged.emit(mvsdk.CameraGetMirror(self.hCamera, 1)) 

    @QtCore.pyqtProperty(int, notify=HMirrorChanged)
    def HMirror(self):
        return mvsdk.CameraGetMirror(self.hCamera, 0)

    @HMirror.setter
    def HMirror(self, mode):
        print('current mode:', mvsdk.CameraGetMirror(self.hCamera, 0))
        print('set mode to', mode)
        if mode == mvsdk.CameraGetMirror(self.hCamera, 0):
            return
        print("Result: ", mvsdk.CameraSetMirror(self.hCamera, 0, mode))
        self.HMirrorChanged.emit(mvsdk.CameraGetMirror(self.hCamera, 0)) 




    @QtCore.pyqtProperty(int, notify=TriggerModeChanged)
    def TriggerMode(self):
        return mvsdk.CameraGetTriggerMode(self.hCamera)

    @TriggerMode.setter
    def TriggerMode(self, trigger_mode):
        print('current trigger mode:', mvsdk.CameraGetTriggerMode(self.hCamera))
        print('set trigger mode to', trigger_mode)
        if trigger_mode == mvsdk.CameraGetTriggerMode(self.hCamera):
            return
        print("Result: ", mvsdk.CameraSetTriggerMode(self.hCamera, trigger_mode))
        self.TriggerModeChanged.emit(mvsdk.CameraGetTriggerMode(self.hCamera)) 


    @QtCore.pyqtProperty(int, notify=AeStateChanged)
    def AeState(self):
        return mvsdk.CameraGetAeState(self.hCamera)

    @AeState.setter
    def AeState(self, state):
        print('current state:', mvsdk.CameraGetAeState(self.hCamera))
        print('set state to', state)
        if state == mvsdk.CameraGetAeState(self.hCamera):
            return
        print("Result: ", mvsdk.CameraSetAeState(self.hCamera, state))
        self.AeStateChanged.emit(mvsdk.CameraGetAeState(self.hCamera)) 

    @QtCore.pyqtProperty(float, notify=AeTargetChanged)
    def AeTarget(self):
        return mvsdk.CameraGetAeTarget(self.hCamera)

    @AeTarget.setter
    def AeTarget(self, target):
        print('current target:', mvsdk.CameraGetAeTarget(self.hCamera))
        print('set target to', target)
        if target == mvsdk.CameraGetAeTarget(self.hCamera):
            return
        print("Result: ", mvsdk.CameraSetAeTarget(self.hCamera, target))
        self.AeTargetChanged.emit(mvsdk.CameraGetAeTarget(self.hCamera)) 

    @QtCore.pyqtProperty(float, notify=ExposureTimeChanged)
    def ExposureTime(self):
        return mvsdk.CameraGetExposureTime(self.hCamera)

    @ExposureTime.setter
    def ExposureTime(self, exposure):
        print('current exposure:', mvsdk.CameraGetExposureTime(self.hCamera))
        print('set exposure to', exposure)
        if exposure == mvsdk.CameraGetExposureTime(self.hCamera):
            return
        print(mvsdk.CameraSetExposureTime(self.hCamera, exposure))
        self.ExposureTimeChanged.emit(mvsdk.CameraGetExposureTime(self.hCamera)) 

    @mvsdk.method(mvsdk.CAMERA_SNAP_PROC)
    def callback(self, hCamera, pRawData, pFrameHead, pContext):
        FrameHead = pFrameHead[0]
        pFrameBuffer = self.pFrameBuffer

        mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
        mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)

        frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3) )

        self.imageChanged.emit(frame)

    def begin(self):
        cap = mvsdk.CameraGetCapability(self.hCamera)
        #PrintCapbility(cap)

        monoCamera = (cap.sIspCapacity.bMonoSensor != 0)
        print('monoCamera', monoCamera)
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)

        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

        print("SetCallbackFunction:", mvsdk.CameraSetCallbackFunction(self.hCamera, self.callback, 0))


    def end(self):
        mvsdk.CameraUnInit(self.hCamera)
        mvsdk.CameraAlignFree(self.pFrameBuffer) 


    def camera_play(self):
        print("play", mvsdk.CameraPlay(self.hCamera))


    def camera_stop(self):
        print(mvsdk.CameraStop(self.hCamera))