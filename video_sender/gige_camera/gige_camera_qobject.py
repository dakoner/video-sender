import signal
import sys
import numpy as np
import pdb
from PyQt5 import QtCore
import mvsdk


class GigECamera(QtCore.QObject):
    imageChanged = QtCore.pyqtSignal(np.ndarray)
    ExposureTimeChanged = QtCore.pyqtSignal(float)

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



    @QtCore.pyqtProperty(float, notify=ExposureTimeChanged)
    def ExposureTime(self):
        return mvsdk.CameraGetExposureTime(self.hCamera)

    @ExposureTime.setter
    def ExposureTime(self, exposure):
        print('set exposure to', exposure)
        if exposure == mvsdk.CameraGetExposureTime(self.hCamera):
            return
        print(mvsdk.CameraSetExposureTime(self.hCamera, exposure))
        self.ExposureTimeChanged.emit(mvsdk.CameraGetExposureTime(self.hCamera)) 

    @mvsdk.method(mvsdk.CAMERA_SNAP_PROC)
    def callback(self, hCamera, pRawData, pFrameHead, pContext):
        print("frame callback")
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

        if monoCamera:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)

        mvsdk.CameraSetTriggerMode(self.hCamera, 2)
        mvsdk.CameraSetAeState(self.hCamera, 0)
        mvsdk.CameraSetExposureTime(self.hCamera, 10)

        mvsdk.CameraPlay(self.hCamera)

        
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)


        mvsdk.CameraSetCallbackFunction(self.hCamera, self.callback, 0)


    def end(self):
        mvsdk.CameraUnInit(self.hCamera)
        mvsdk.CameraAlignFree(self.pFrameBuffer) 