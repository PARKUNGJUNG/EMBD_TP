import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog
from PyQt5.QtGui import QPixmap
from pathlib import Path
import face_recognition
import pickle
from collections import Counter
from PIL import Image, ImageDraw

DEFAULT_ENCODINGS_PATH = Path("output/encodings.pkl")
BOUNDING_BOX_COLOR = "blue"
TEXT_COLOR = "white"

class FaceRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Face Recognition App')
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel(self)
        self.label.setGeometry(50, 50, 700, 400)

        self.btn = QPushButton('Open Image', self)
        self.btn.setGeometry(350, 500, 100, 30)
        self.btn.clicked.connect(self.open_image)

    def open_image(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.xpm *.jpg)", options=options)
        if fileName:
            self.recognize_faces(fileName)

    def recognize_faces(self, image_location):
        with DEFAULT_ENCODINGS_PATH.open(mode="rb") as f:
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
        pillow_image.save("recognized.jpg")
        self.label.setPixmap(QPixmap("recognized.jpg"))

    def _recognize_face(self, unknown_encoding, loaded_encodings):
        boolean_matches = face_recognition.compare_faces(loaded_encodings["encodings"], unknown_encoding)
        votes = Counter(name for match, name in zip(boolean_matches, loaded_encodings["names"]) if match)
        if votes:
            return votes.most_common(1)[0][0]

    def _display_face(self, draw, bounding_box, name):
        top, right, bottom, left = bounding_box
        draw.rectangle(((left, top), (right, bottom)), outline=BOUNDING_BOX_COLOR)
        text_left, text_top, text_right, text_bottom = draw.textbbox((left, bottom), name)
        draw.rectangle(((text_left, text_top), (text_right, text_bottom)), fill="blue", outline="blue")
        draw.text((text_left, text_top), name, fill="white")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FaceRecognitionApp()
    ex.show()
    sys.exit(app.exec_())
