import os
import time
import sys
import cv2  # OpenCV for webcam integration
import pickle  # for encoding models
import numpy as np  # for image array processing
import RPi.GPIO as GPIO
from collections import Counter
from PIL import Image
from huskylib import HuskyLensLibrary
from face_recognition import face_locations, face_encodings, compare_faces

# 전역 변수
husky = None  # HuskyLens 객체
HOME_DIR = os.path.expanduser("~")  # 사용자 홈 디렉토리 경로
SCREENSHOT_DIR = os.path.join(HOME_DIR, "HNUCE", "screenshot")  # 스크린샷 저장 경로
SERVO_PIN = 11  # 서보 모터 GPIO 핀 번호
WEBCAM_SAVE_PATH = os.path.join(SCREENSHOT_DIR, "webcam_snapshot.jpg")  # 웹캠 캡처 이미지 저장 경로
ENCODINGS_PATH = os.path.join(HOME_DIR, "HNUCE", "encodings.pkl")  # 얼굴 인코딩 데이터 경로


# 오류 메시지 출력 후 종료 함수
def fail_exit(message):
    """오류 메시지를 출력하고 프로그램 종료"""
    print(f"[ERROR] {message}")
    GPIO.cleanup()
    sys.exit(1)


# 초기 설정 함수
def setup():
    global husky
    print("초기 설정 중...")

    # 스크린샷 저장 폴더 생성
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)
        print(f"[INFO] 스크린샷 저장 디렉토리 생성 완료: {SCREENSHOT_DIR}")

    # HuskyLens Serial 연결
    print("[INFO] HuskyLens Serial 연결 중...")
    husky = HuskyLensLibrary("SERIAL", comPort="/dev/ttyS0", speed=9600)
    if husky.knock():
        print("[INFO] HuskyLens Serial 연결 성공!")
    else:
        fail_exit("HuskyLens 연결 실패: Serial 설정 확인 필요.")

    # GPIO 초기화 및 서보 모터 설정
    print("[INFO] GPIO 및 서보 설정 중...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    global servo
    servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz PWM 동작
    servo.start(0)
    print("[INFO] 초기 설정 완료.")


# 서보 모터를 특정 각도로 회전시키는 함수
def rotate_servo(angle):
    """서보 모터 회전"""
    duty_cycle = angle / 18.0 + 2
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)


# HuskyLens 학습된 얼굴 감지
def detect_face(data):
    """HuskyLens의 감지 데이터를 분석하여 학습된 얼굴 확인"""
    if not data:
        print("[DEBUG] 감지 데이터 없음")
        return False

    for item in data:
        if hasattr(item, "ID") and item.ID > 0:  # 학습된 ID인지 확인
            print(f"[INFO] 학습된 얼굴 감지 - ID: {item.ID}")
            return True
    print("[DEBUG] 학습된 얼굴 감지되지 않음")
    return False


# USB 웹캠으로 이미지 캡처
def capture_webcam_image(output_path=WEBCAM_SAVE_PATH):
    """USB 웹캠에서 실시간 이미지 캡처"""
    print("[INFO] USB 웹캠으로 이미지 캡처 시도 중...")
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        fail_exit("웹캠에 접근할 수 없습니다. 연결을 확인하세요.")

    ret, frame = cam.read()
    if ret:
        cv2.imwrite(output_path, frame)
        print(f"[INFO] USB 웹캠 이미지 캡처 완료: {output_path}")
    else:
        fail_exit("웹캠에서 이미지를 캡처하는 데 실패했습니다.")

    cam.release()
    return output_path


# 얼굴 인식 함수 (결과 반환)
def recognize_faces_with_result(image_location, model="hog"):
    """웹캠에서 캡처한 이미지를 사용하여 얼굴을 인식"""
    try:
        with open(ENCODINGS_PATH, "rb") as f:
            loaded_encodings = pickle.load(f)

        image = np.array(Image.open(image_location).convert("RGB"))
        face_locations_list = face_locations(image, model=model)
        face_encodings_list = face_encodings(image, face_locations_list)

        if not face_locations_list:
            print("[DEBUG] 얼굴이 감지되지 않았습니다.")
            return None

        for face_encoding in face_encodings_list:
            matches = compare_faces(loaded_encodings["encodings"], face_encoding)
            name_votes = Counter(
                name for match, name in zip(matches, loaded_encodings["names"]) if match
            )
            if name_votes:
                recognized_name = name_votes.most_common(1)[0][0]
                return recognized_name
            else:
                return "Unknown"
    except Exception as e:
        print(f"[ERROR] 얼굴 인식 중 오류 발생: {e}")
        return "Unknown"


# 2차 검증 - 얼굴 인식 수행
def secondary_face_verification_with_webcam():
    """웹캠 캡처 이미지를 사용하여 추가 얼굴 검증 수행"""
    image_path = capture_webcam_image()
    print("[INFO] 2차 인증 시작...")
    result = recognize_faces_with_result(image_location=image_path)
    if result == "Unknown" or result is None:
        print("[ERROR] 2차 인증 실패: 얼굴이 인식되지 않거나 권한이 없는 사용자입니다.")
        return False
    print(f"[INFO] 2차 인증 성공: 얼굴 인증 완료! (사용자: {result})")
    rotate_servo(90)  # 서보 모터 작동
    time.sleep(1)
    rotate_servo(0)
    return True


# 메인 루프
def loop():
    print("[INFO] 메인 루프 실행 중...")
    try:
        while True:
            # HuskyLens에서 학습된 얼굴 요청
            print("[DEBUG] HuskyLens 데이터 요청 중...")
            husky_data = husky.requestAll()
            if detect_face(husky_data):
                print("[INFO] 1차 인증: 학습된 얼굴 확인됨.")
                if not secondary_face_verification_with_webcam():
                    print("[INFO] 2차 인증 실패: 1차 인증으로 복귀.")
                    continue  # 1차 인증 루프로 복귀
                print("[INFO] 인증 완료: 정상 작동 중.")  # 2차 인증 성공
            else:
                print("[INFO] 학습된 얼굴 없음. 대기 중...")
            time.sleep(0.5)  # 대기 시간 설정
    except KeyboardInterrupt:
        print("[INFO] 프로그램 종료 중...")
        GPIO.cleanup()
        sys.exit(0)


# 프로그램 실행
if __name__ == "__main__":
    setup()
    loop()
