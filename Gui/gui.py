import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk  # Progress Bar를 위한 ttk 모듈 사용
import threading
import time
from AI import detector


class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition App")
        self.root.geometry("400x300")  # GUI 창의 크기를 조정

        # Create the GUI elements
        self.create_widgets()

    def create_widgets(self):
        # 상태 표시 라벨
        self.status_label = tk.Label(self.root, text="Idle", fg="blue", font=("Arial", 12))
        self.status_label.grid(row=0, column=0, columnspan=2, pady=10)

        # 진행 상황 표시바 (Progress Bar)
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.grid(row=1, column=0, columnspan=2, pady=10)

        # 학습 버튼
        self.train_button = tk.Button(self.root, text="Train", command=self.train_faces)
        self.train_button.grid(row=2, column=0, padx=10, pady=10)

        # 검증 버튼
        self.validate_button = tk.Button(self.root, text="Validate", command=self.validate_faces)
        self.validate_button.grid(row=2, column=1, padx=10, pady=10)

        # 테스트 버튼
        self.test_button = tk.Button(self.root, text="Test", command=self.test_faces)
        self.test_button.grid(row=3, column=0, padx=10, pady=10)

        # 비교 버튼
        self.compare_button = tk.Button(self.root, text="Compare", command=self.compare_faces)
        self.compare_button.grid(row=3, column=1, padx=10, pady=10)

    def update_status(self, message):
        """상태 표시 라벨을 업데이트"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def update_progress(self, value):
        """진행 상황 표시바를 업데이트"""
        self.progress['value'] = value
        self.root.update_idletasks()

    def run_in_thread(self, func, *args):
        """비동기 실행을 위해 별도의 스레드에서 작업 수행"""
        threading.Thread(target=func, args=args).start()

    def simulate_task(self):
        """Progress bar 테스트용 임시 작업 시뮬레이션"""
        for i in range(101):
            self.update_progress(i)
            time.sleep(0.05)

    def train_faces(self):
        """detector.py의 encode_known_faces 함수를 호출 (비동기 처리)"""
        self.update_status("Training started...")
        self.run_in_thread(self._train_faces)

    def _train_faces(self):
        self.simulate_task()  # 실제 detector.py 작업 대신 임시 작업
        detector.encode_known_faces(model="hog")
        self.update_status("Training complete")
        messagebox.showinfo("Success", "Face training complete")

    def validate_faces(self):
        """detector.py의 validate 함수를 호출 (비동기 처리)"""
        self.update_status("Validation started...")
        self.run_in_thread(self._validate_faces)

    def _validate_faces(self):
        self.simulate_task()  # 실제 detector.py 작업 대신 임시 작업
        detector.validate(model="hog")
        self.update_status("Validation complete")
        messagebox.showinfo("Success", "Validation complete")

    def test_faces(self):
        """detector.py의 recognize_faces 함수를 호출하여 테스트 (비동기 처리)"""
        file_path = filedialog.askopenfilename(title="Select Image for Testing",
                                               filetypes=[("Image Files",
                                                           "*.jpg *.jpeg *.png *.bmp *.tiff *.gif *.jfif *.webp *.svg *.ico *.heic *.heif"),
                                                          ("All Files", "*.*")])
        if file_path:
            self.update_status("Testing started...")
            self.run_in_thread(self._test_faces, file_path)

    def _test_faces(self, file_path):
        self.simulate_task()  # 실제 detector.py 작업 대신 임시 작업
        detector.recognize_faces(image_location=file_path, model="hog")
        self.update_status("Testing complete")
        messagebox.showinfo("Success", "Face test complete")

    def compare_faces(self):
        """detector.py의 compare_faces 함수를 호출하여 두 이미지를 비교 (비동기 처리)"""
        file_path1 = filedialog.askopenfilename(title="Select First Image",
                                                filetypes=[("Image Files",
                                                            "*.jpg *.jpeg *.png *.bmp *.tiff *.gif *.jfif *.webp *.svg *.ico *.heic *.heif"),
                                                           ("All Files", "*.*")])

        file_path2 = filedialog.askopenfilename(title="Select Second Image",
                                                filetypes=[("Image Files",
                                                            "*.jpg *.jpeg *.png *.bmp *.tiff *.gif *.jfif *.webp *.svg *.ico *.heic *.heif"),
                                                           ("All Files", "*.*")])

        if file_path1 and file_path2:
            self.update_status("Comparison started...")
            self.run_in_thread(self._compare_faces, file_path1, file_path2)

    def _compare_faces(self, file_path1, file_path2):
        self.simulate_task()  # 실제 detector.py 작업 대신 임시 작업
        detector.compare_faces(image1_path=file_path1, image2_path=file_path2, model="hog")
        self.update_status("Comparison complete")
        messagebox.showinfo("Success", "Face comparison complete")


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
