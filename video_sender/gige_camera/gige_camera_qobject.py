import signal
import sys
import numpy as np
import pdb
from PyQt5 import QtCore
import mvsdk


class Worker(QtCore.QThread):
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)

    def __init__(self, hCamera):
        super().__init__()
        self.hCamera = hCamera
        
        # 获取相机特性描述
        cap = mvsdk.CameraGetCapability(self.hCamera)
        #PrintCapbility(cap)

        # 判断是黑白相机还是彩色相机
        monoCamera = (cap.sIspCapacity.bMonoSensor != 0)

        # 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)

        # 相机模式切换成连续采集
        mvsdk.CameraSetTriggerMode(self.hCamera, 0)

        # 手动曝光，曝光时间30ms
        mvsdk.CameraSetAeState(self.hCamera, 0)
        mvsdk.CameraSetExposureTime(self.hCamera, 0)

        # 让SDK内部取图线程开始工作
        mvsdk.CameraPlay(self.hCamera)

        
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)

        # 分配RGB buffer，用来存放ISP输出的图像
        # 备注：从相机传输到PC端的是RAW数据，在PC端通过软件ISP转为RGB数据（如果是黑白相机就不需要转换格式，但是ISP还有其它处理，所以也需要分配这个buffer）
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

    @QtCore.pyqtSlot()
    def run(self):
        while True:
            self.acquire_callback()
        

    def acquire_callback(self):
        # 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配

        # 从相机取一帧图片
        try:
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 2000)
            mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
            frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3) )

            self.imageChanged.emit(frame, frame.shape[1], frame.shape[0], frame.shape[1])

        except mvsdk.CameraException as e:
            print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message) )


class GigECamera(QtCore.QObject):
    exposureChanged = QtCore.pyqtSignal(float)
    autoExposureModeChanged = QtCore.pyqtSignal(bool)
    acquisitionModeChanged = QtCore.pyqtSignal(bool)
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)

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

        
        # # 打开相机
        self.hCamera = 0
        try:
            self.hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
            return

        self.worker = None

    def callback(self, d, w, h, s):
        self.imageChanged.emit(d, w, h, s)

    def begin(self):
        self.worker = Worker(self.hCamera)
        self.worker.imageChanged.connect(self.callback, QtCore.Qt.DirectConnection)
        self.worker.start()

    def end(self):
        self.worker.terminate()
        self.worker = None
        self.cap.release()

    # @QtCore.pyqtProperty(str, notify=acquisitionModeChanged)
    # def acquisitionMode(self):
    #     return self.camera.AcquisitionMode.ToString()

    # @acquisitionMode.setter
    # def acquisitionMode(self, acquisitionMode):
    #     node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionMode'))
    #     acquisitionMode_value = node_acquisition_mode.GetEntryByName(acquisitionMode).GetValue()
    #     if acquisitionMode_value == node_acquisition_mode.GetIntValue(): return
    #     node_acquisition_mode.SetIntValue(acquisitionMode_value)
    #     self.acquisitionModeChanged.emit(node_acquisition_mode.GetIntValue()) 



    # @QtCore.pyqtProperty(bool)#, notify=autoExposureModeChanged)
    # def autoExposureMode(self):
    #     try:
    #         node_autoExposure_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('ExposureAuto'))    
    #         currentValue = node_autoExposure_mode.GetIntValue()
    #         if currentValue == PySpin.ExposureAuto_Off: returnValue= False
    #         elif currentValue == PySpin.ExposureAuto_Continuous: returnValue= True
    #         return returnValue
    #     except:
    #         import traceback
    #         traceback.print_exc()

    # @autoExposureMode.setter
    # def autoExposureMode(self, autoExposureMode):
    #     currentValue = self.camera.ExposureAuto.GetValue()
    #     if autoExposureMode is False:
    #         if currentValue is PySpin.ExposureAuto_Off: return
    #         self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

    #     elif autoExposureMode is True:
    #         if currentValue is PySpin.ExposureAuto_Continuous: return
    #         self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)

    #     currentValue = self.camera.ExposureAuto.GetValue()

    #     if currentValue == PySpin.ExposureAuto_Off: returnValue= False
    #     elif currentValue == PySpin.ExposureAuto_Continuous: returnValue= True
    #     self.autoExposureModeChanged.emit(returnValue) 

    # @QtCore.pyqtProperty(float, notify=exposureChanged)
    # def exposure(self):
    #     return self.camera.ExposureTime.GetValue()

    # @exposure.setter
    # def exposure(self, exposure):
    #     print("Autoexposure value:",  self.camera.ExposureAuto.GetValue())
    #     if exposure == self.camera.ExposureTime.GetValue():
    #         return
    #     self.camera.ExposureTime.SetValue(exposure)
    #     self.exposureChanged.emit(self.camera.ExposureTime.GetValue()) 
        


