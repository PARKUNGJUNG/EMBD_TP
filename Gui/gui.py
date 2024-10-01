import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from pathlib import Path
import face_recognition
import pickle
from PIL import Image, ImageDraw
from detector import encode_known_faces, recognize_faces, validate

class FaceRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Face Recognition App')
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel(self)
        self.label.setGeometry(50, 50, 700, 400)

        self.btnLoadImage = QPushButton('Load Image', self)
        self.btnLoadImage.setGeometry(50, 500, 100, 30)
        self.btnLoadImage.clicked.connect(self.loadImage)

        self.btnRecognize = QPushButton('Recognize Faces', self)
        self.btnRecognize.setGeometry(200, 500, 150, 30)
        self.btnRecognize.clicked.connect(self.recognizeFaces)

        self.imagePath = None

    def loadImage(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*);;JPEG (*.jpg;*.jpeg);;PNG (*.png)", options=options)
        if fileName:
            self.imagePath = fileName
            pixmap = QPixmap(fileName)
            self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height()))

    def recognizeFaces(self):
        if self.imagePath:
            recognize_faces(self.imagePath)
        else:
            print("No image loaded")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FaceRecognitionApp()
    ex.show()
    sys.exit(app.exec_())
