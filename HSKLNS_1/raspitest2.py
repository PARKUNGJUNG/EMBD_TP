import os
import time
import sys
import cv2  # OpenCV for webcam integration
import pickle  # for encoding models
import numpy as np  # for image array processing
import RPi.GPIO as GPIO
from collections import Counter
from PIL import Image
from face_recognition import face_locations, face_encodings, compare_faces

# 전역 변수
HOME_DIR = os.path.expanduser("~")  # 사용자 홈 디렉토리 경로
SCREENSHOT_DIR = os.path.join(HOME_DIR, "HNUCE", "screenshot")  # 스크린샷 저장 경로
SERVO_PIN = 18  # 서보 모터 GPIO 핀 번호
WEBCAM_SAVE_PATH = os.path.join(SCREENSHOT_DIR, "webcam_snapshot.jpg")  # 웹캠 캡처 이미지 저장 경로
ENCODINGS_PATH = os.path.join(HOME_DIR, "output", "encodings.pkl")  # 얼굴 인코딩 데이터 경로


# 오류 메시지 출력 후 종료 함수
def fail_exit(message):
    """오류 메시지를 출력하고 프로그램 종료"""
    print(f"[ERROR] {message}")
    GPIO.cleanup()
    sys.exit(1)


# 초기 설정 함수
def setup():
    GPIO.cleanup()
    print("초기 설정 중...")

    # 스크린샷 저장 폴더 생성
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)
        print(f"[INFO] 스크린샷 저장 디렉토리 생성 완료: {SCREENSHOT_DIR}")

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


# 2차 검증 - 얼굴 인식 수행 및 서보 작동 추가
def secondary_face_verification_with_webcam():
    """웹캠 캡처 이미지를 사용하여 추가 얼굴 검증 수행"""
    image_path = capture_webcam_image()  # 웹캠으로 사진 촬영
    print("[INFO] 사용자 인증 시작...")

    result = recognize_faces_with_result(image_location=image_path)  # 얼굴 인식
    if result == "Unknown" or result is None:
        print("[ERROR] 사용자 인증 실패: 얼굴이 인식되지 않거나 권한이 없는 사용자입니다.")
        return False  # 인증 실패

    print(f"[INFO] 사용자 인증 성공: 얼굴 인증 완료! (사용자: {result})")

    # 서보 모터 회전
    rotate_servo(80)  # 문 열기 상태 (90도 회전)
    time.sleep(10)  # 5초간 문 열기 상태 유지
    rotate_servo(0)  # 문 닫기 상태 (0도 회전)

    return True  # 인증 성공


# 메인 루프
def loop():
    print("[INFO] 메인 루프 실행 중...")
    try:
        while True:

            # 1차 인증 (HuskyLens 학습된 얼굴 감지)
            if secondary_face_verification_with_webcam():
                print("[INFO] 사용자 인증: 학습된 얼굴 확인됨.")

            else:
                print("[INFO] 학습된 얼굴 없음 - 대기 중...")
                continue
            time.sleep(0.5)  # 각 검증 루프 간 짧은 대기
    except KeyboardInterrupt:
        # 사용자 인터럽트 시 프로그램 안전 종료
        print("[INFO] 프로그램 종료 중...")
        GPIO.cleanup()
        sys.exit(0)


# 프로그램 실행 진입점
if __name__ == "__main__":
    setup()
    loop()
