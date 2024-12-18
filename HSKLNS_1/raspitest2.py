import cv2
import numpy as np
import RPi.GPIO as GPIO
import os

# 기본 설정 및 경로
HOME_DIR = "/home/pi"
SCREENSHOT_DIR = os.path.join(HOME_DIR, "screenshots")
SERVO_PIN = 17
WEBCAM_SAVE_PATH = os.path.join(SCREENSHOT_DIR, "webcam.jpg")
ENCODINGS_PATH = os.path.join(HOME_DIR, "encodings.pkl")


def fail_exit():
    print("프로그램 중단")
    GPIO.cleanup()
    exit(1)


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    # 서보모터 PWM 설정
    global pwm
    pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz
    pwm.start(0)


def rotate_servo(angle):
    duty = angle / 18.0 + 2
    GPIO.output(SERVO_PIN, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)
    GPIO.output(SERVO_PIN, False)
    pwm.ChangeDutyCycle(0)


def detect_face(image):
    # 얼굴 탐지 구현
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return len(faces) > 0


def capture_webcam_image(save_path):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        fail_exit()
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(save_path, frame)
    cap.release()
    return frame


def recognize_faces_with_result(encodings_path, image):
    # 얼굴 인식 로직
    # Encoding 파일 읽기 및 상대적인 검증 추가
    return True  # 성공적으로 인식되었다고 가정


def secondary_face_verification_with_webcam():
    image = capture_webcam_image(WEBCAM_SAVE_PATH)
    if detect_face(image):
        return recognize_faces_with_result(ENCODINGS_PATH, image)
    else:
        return False


def loop():
    while True:
        print("웹캠이 작동 중입니다...")
        if secondary_face_verification_with_webcam():
            print("얼굴 인증 성공!")
            rotate_servo(90)  # 서보모터를 회전
        else:
            print("얼굴 인증 실패")
