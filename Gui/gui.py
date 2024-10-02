import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap
from pathlib import Path
import face_recognition
import pickle
from PIL import Image, ImageDraw
from collections import Counter
from AI.detector import encode_known_faces, recognize_faces, validate

DEFAULT_ENCODINGS_PATH = Path("output/encodings.pkl")

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

        self.btnSaveImage = QPushButton('Save Image', self)
        self.btnSaveImage.setGeometry(400, 500, 100, 30)
        self.btnSaveImage.clicked.connect(self.saveImage)

        self.btnTrain = QPushButton('Train', self)
        self.btnTrain.setGeometry(550, 500, 100, 30)
        self.btnTrain.clicked.connect(self.trainModel)

        self.btnValidate = QPushButton('Validate', self)
        self.btnValidate.setGeometry(700, 500, 100, 30)
        self.btnValidate.clicked.connect(self.validateModel)

        self.imagePath = None
        self.recognizedImage = None

    def loadImage(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*);;JPEG (*.jpg;*.jpeg);;PNG (*.png)", options=options)
        if fileName:
            self.imagePath = fileName
            pixmap = QPixmap(fileName)
            self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height()))
            QMessageBox.information(self, "Image Loaded", "Image loaded successfully!")

    def recognizeFaces(self):
        if self.imagePath:
            self.recognizedImage = self.recognize_faces(self.imagePath)
            pixmap = QPixmap(self.recognizedImage)
            self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height()))
            QMessageBox.information(self, "Recognition Complete", "Faces recognized successfully!")
        else:
            QMessageBox.warning(self, "No Image", "No image loaded")

    def recognize_faces(self, image_location):
        with open(DEFAULT_ENCODINGS_PATH, "rb") as f:
            loaded_encodings = pickle.load(f)

        input_image = face_recognition.load_image_file(image_location)
        input_face_locations = face_recognition.face_locations(input_image, model="hog")
        input_face_encodings = face_recognition.face_encodings(input_image, input_face_locations)

        pillow_image = Image.fromarray(input_image)
        draw = ImageDraw.Draw(pillow_image)

        for bounding_box, unknown_encoding in zip(input_face_locations, input_face_encodings):
            name = self._recognize_face(unknown_encoding, loaded_encodings)
            if not name:
                name = "Unknown"
            self._display_face(draw, bounding_box, name)

        del draw
        pillow_image.save("recognized_image.png")
        return "recognized_image.png"

    def _recognize_face(self, unknown_encoding, loaded_encodings):
        boolean_matches = face_recognition.compare_faces(loaded_encodings["encodings"], unknown_encoding)
        votes = Counter(name for match, name in zip(boolean_matches, loaded_encodings["names"]) if match)
        if votes:
            return votes.most_common(1)[0][0]

    def _display_face(self, draw, bounding_box, name):
        top, right, bottom, left = bounding_box
        draw.rectangle(((left, top), (right, bottom)), outline="blue")
        text_left, text_top, text_right, text_bottom = draw.textbbox((left, bottom), name)
        draw.rectangle(((text_left, text_top), (text_right, text_bottom)), fill="blue", outline="blue")
        draw.text((text_left, text_top), name, fill="white")

    def saveImage(self):
        if self.recognizedImage:
            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG (*.png);;JPEG (*.jpg;*.jpeg)", options=options)
            if fileName:
                Image.open(self.recognizedImage).save(fileName)
                QMessageBox.information(self, "Image Saved", "Image saved successfully!")
        else:
            QMessageBox.warning(self, "No Image", "No recognized image to save")

    def trainModel(self):
        encode_known_faces(model="hog")
        QMessageBox.information(self, "Training Complete", "Model trained successfully!")

    def validateModel(self):
        validate(model="hog")
        QMessageBox.information(self, "Validation Complete", "Model validated successfully!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FaceRecognitionApp()
    ex.show()
    sys.exit(app.exec_())
