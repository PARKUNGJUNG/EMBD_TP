import tkinter as tk
from tkinter import filedialog, messagebox
import AI.detector as detector  # detector.py를 import하여 기능 사용
import os


class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition App")

        # Create the GUI elements
        self.create_widgets()

    def create_widgets(self):
        # 학습 버튼
        self.train_button = tk.Button(self.root, text="Train", command=self.train_faces)
        self.train_button.grid(row=0, column=0, padx=10, pady=10)

        # 검증 버튼
        self.validate_button = tk.Button(self.root, text="Validate", command=self.validate_faces)
        self.validate_button.grid(row=0, column=1, padx=10, pady=10)

        # 테스트 버튼
        self.test_button = tk.Button(self.root, text="Test", command=self.test_faces)
        self.test_button.grid(row=1, column=0, padx=10, pady=10)

        # 비교 버튼
        self.compare_button = tk.Button(self.root, text="Compare", command=self.compare_faces)
        self.compare_button.grid(row=1, column=1, padx=10, pady=10)

    def train_faces(self):
        """detector.py의 encode_known_faces 함수를 호출"""
        detector.encode_known_faces(model="hog")
        messagebox.showinfo("Success", "Face training complete")

    def validate_faces(self):
        """detector.py의 validate 함수를 호출"""
        detector.validate(model="hog")
        messagebox.showinfo("Success", "Validation complete")

    def test_faces(self):
        """detector.py의 recognize_faces 함수를 호출하여 테스트"""
        file_path = filedialog.askopenfilename(title="Select Image for Testing", filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if file_path:
            detector.recognize_faces(image_location=file_path, model="hog")

    def compare_faces(self):
        """detector.py의 compare_faces 함수를 호출하여 두 이미지를 비교"""
        file_path1 = filedialog.askopenfilename(title="Select First Image", filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        file_path2 = filedialog.askopenfilename(title="Select Second Image", filetypes=[("Image Files", "*.jpg *.jpeg *.png")])

        if file_path1 and file_path2:
            detector.compare_faces(image1_path=file_path1, image2_path=file_path2, model="hog")


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
