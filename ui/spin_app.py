from enum import Enum
import PySpin
import signal
import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from spin_widget import SpinWidget
from pyspin_camera import PySpinCamera



        
class QApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super(QApplication, self).__init__(*args, **kwargs)
        
        self.main_widget = SpinWidget()
        self.main_widget.show()
        

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.exec_()

