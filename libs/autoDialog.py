try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

import json

from libs.utils import newIcon

BB = QDialogButtonBox


class Worker(QThread):
    progressBarValue = pyqtSignal(int)  # 更新进度条
    listValue = pyqtSignal(str)
    endsignal = pyqtSignal(int, str)
    handle = 0

    def __init__(self, ocr, mImgList, mainThread, model):
        super(Worker, self).__init__()
        self.ocr = ocr
        self.mImgList = mImgList
        self.mainThread = mainThread
        self.model = model

    def run(self):
        try:

            findex = 0
            for Imgpath in self.mImgList:
                if self.handle == 0:
                    self.listValue.emit(Imgpath)
                    if self.model == 'paddle':
                        self.result_dic = self.ocr.ocr(Imgpath, cls=True, det=True)

                    # 结果保存
                    if self.result_dic is None or len(self.result_dic) == 0:
                        print('Can not recognise file  is :  ', Imgpath)
                        pass
                    else:
                        for res in self.result_dic:
                            chars = res[1][0]
                            cond = res[1][1]
                            posi = res[0]
                            self.listValue.emit("文字:" + chars + " 置信度:" + str(cond) + " 坐标:" + json.dumps(posi))
                        # self.filePath 存在
                        self.mainThread.result_dic = self.result_dic
                        self.mainThread.filePath = Imgpath  # 文件路径
                        # 保存
                        self.mainThread.saveFile(mode='Auto')
                    findex += 1
                    self.progressBarValue.emit(findex)
                else:
                    break
            self.endsignal.emit(0, "readAll")
            self.exec()
        except Exception as e:
            print(e)
            raise


class AutoDialog(QDialog):

    def __init__(self, text="Enter object label", parent=None, ocr=None, mImgList=None, lenbar=0):
        super(AutoDialog, self).__init__(parent)
        self.setFixedWidth(1000)
        self.parent = parent
        self.ocr = ocr
        self.mImgList = mImgList
        self.pb = QProgressBar()
        self.pb.setRange(0, lenbar)
        self.pb.setValue(0)

        layout = QVBoxLayout()
        layout.addWidget(self.pb)
        self.model = 'paddle'
        self.listWidget = QListWidget(self)
        layout.addWidget(self.listWidget)

        self.buttonBox = bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)
        bb.button(BB.Ok).setIcon(newIcon('done'))
        bb.button(BB.Cancel).setIcon(newIcon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        bb.button(BB.Ok).setEnabled(False)

        self.setLayout(layout)
        self.setWindowTitle("自动标注中")
        self.setWindowModality(Qt.ApplicationModal)

        # self.setWindowFlags(Qt.WindowCloseButtonHint)

        self.thread_1 = Worker(self.ocr, self.mImgList, self.parent, 'paddle')
        self.thread_1.progressBarValue.connect(self.handleProgressBarSingal)
        self.thread_1.listValue.connect(self.handleListWidgetSingal)
        self.thread_1.endsignal.connect(self.handleEndsignalSignal)

    def handleProgressBarSingal(self, i):
        self.pb.setValue(i)

    def handleListWidgetSingal(self, i):
        self.listWidget.addItem(i)
        titem = self.listWidget.item(self.listWidget.count() - 1)
        self.listWidget.scrollToItem(titem)

    def handleEndsignalSignal(self, i, str):
        if i == 0 and str == "readAll":
            self.buttonBox.button(BB.Ok).setEnabled(True)
            self.buttonBox.button(BB.Cancel).setEnabled(False)

    def reject(self):
        print("reject")
        self.thread_1.handle = -1
        self.thread_1.quit()
        # del self.thread_1
        # if self.thread_1.isRunning():
        #     self.thread_1.terminate()
        # self.thread_1.quit()
        # super(AutoDialog,self).reject()
        while not self.thread_1.isFinished():
            pass
        self.accept()

    def validate(self):
        self.accept()

    def postProcess(self):
        try:
            self.edit.setText(self.edit.text().trimmed())
            # print(self.edit.text())
        except AttributeError:
            # PyQt5: AttributeError: 'str' object has no attribute 'trimmed'
            self.edit.setText(self.edit.text())
            print(self.edit.text())

    def popUp(self):
        self.thread_1.start()
        return 1 if self.exec_() else None

    def closeEvent(self, event):
        print("???")
        # if self.thread_1.isRunning():
        #     self.thread_1.quit()
        #     # 强制
        #     # self._thread.terminate()
        # # del self.thread_1
        # super(AutoDialog, self).closeEvent(event)
        self.reject()
