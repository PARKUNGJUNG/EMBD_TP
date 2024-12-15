import os
import time
import shutil
import sys
import cv2  # OpenCV for webcam integration
import RPi.GPIO as GPIO
from huskylib import HuskyLensLibrary
from detector import recognize_faces

# 전역 변수
husky = None  # HuskyLens 객체
HOME_DIR = os.path.expanduser("~")  # 사용자 홈 디렉토리 경로
SCREENSHOT_DIR = os.path.join(HOME_DIR, "HNUCE", "screenshot")  # 스크린샷 저장 경로
SERVO_PIN = 11  # 서보 모터 GPIO 핀 번호
WEBCAM_SAVE_PATH = os.path.join(SCREENSHOT_DIR, "webcam_snapshot.jpg")  # 웹캠 캡처 이미지 저장 경로


# 오류 메시지 출력 후 종료 함수
def fail_exit(message):
    """오류 메시지를 출력하고 프로그램 종료"""
    print(f"[ERROR] {message}")
    sys.exit(1)


# 초기 설정 함수
def setup():
    global husky
    print("초기 설정 중...")

    # 스크린샷 저장 폴더 생성
    try:
        if not os.path.exists(SCREENSHOT_DIR):
            os.makedirs(SCREENSHOT_DIR)
        print(f"[INFO] 스크린샷 저장 디렉토리 확인 완료: {SCREENSHOT_DIR}")
    except Exception as e:
        fail_exit(f"스크린샷 저장 디렉토리 생성 실패: {e}")

    # HuskyLens Serial 연결
    try:
        print("[INFO] HuskyLens Serial 연결 중...")
        husky = HuskyLensLibrary("SERIAL", comPort="/dev/ttyS0", speed=9600)

        if husky.knock():
            print("[INFO] HuskyLens Serial 연결 성공!")
        else:
            fail_exit("HuskyLens 연결 실패: Serial 설정을 확인해주세요.")
    except Exception as e:
        fail_exit(f"HuskyLens 연결 중 오류 발생: {e}")

    # GPIO 초기화
    try:
        print("[INFO] GPIO 설정 중...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SERVO_PIN, GPIO.OUT)

        # 서보 PWM 설정
        global servo
        servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz PWM 동작
        servo.start(0)
        print("[INFO] GPIO 및 서보 설정 성공")
    except Exception as e:
        fail_exit(f"GPIO 초기화 중 오류 발생: {e}")

    print("[INFO] 초기 설정 완료 - 시스템 준비 완료!")


# 서보 모터를 특정 각도로 회전시키는 함수
def rotate_servo(angle):
    """서보 모터 회전"""
    try:
        print(f"[DEBUG] 서보 모터 {angle}도 회전 중...")
        duty_cycle = angle / 18.0 + 2
        servo.ChangeDutyCycle(duty_cycle)
        time.sleep(0.5)
        servo.ChangeDutyCycle(0)
        print(f"[DEBUG] 서보 모터 {angle}도 회전 완료")
    except Exception as e:
        fail_exit(f"서보 모터 제어 중 오류 발생: {e}")


# HuskyLens 학습된 얼굴 감지
def detect_face(data):
    """HuskyLens의 감지 데이터를 분석하여 학습된 얼굴 확인"""
    print("[DEBUG] HuskyLens 데이터 분석 중...")
    if not data:
        print("[DEBUG] 감지 데이터 없음")
        return False

    try:
        for item in data:
            if hasattr(item, "ID") and item.ID > 0:  # 학습된 ID인지 확인
                print(f"[INFO] 학습된 얼굴 감지 - ID: {item.ID}")
                return True
        print("[DEBUG] 학습된 얼굴 감지되지 않음")
        return False
    except Exception as e:
        fail_exit(f"HuskyLens 데이터 분석 중 오류 발생: {e}")


# USB 웹캠으로 이미지 캡처
def capture_webcam_image(output_path=WEBCAM_SAVE_PATH):
    """USB 웹캠에서 실시간 이미지 캡처"""
    try:
        print("[INFO] USB 웹캠으로 이미지 캡처 시도 중...")
        cam = cv2.VideoCapture(0)  # 0번 장치를 통해 웹캠 접근
        if not cam.isOpened():
            fail_exit("웹캠에 접근할 수 없습니다. 연결을 확인하세요.")

        ret, frame = cam.read()
        if ret:
            cv2.imwrite(output_path, frame)
            print(f"[INFO] USB 웹캠 이미지 캡처 완료: {output_path}")
        else:
            fail_exit("웹캠에서 이미지를 캡처하는 데 실패했습니다.")

        cam.release()
        cv2.destroyAllWindows()
        return output_path
    except Exception as e:
        fail_exit(f"웹캠 이미지 캡처 중 오류 발생: {e}")


# 2차 검증 - 웹캠 이미지 기반
def secondary_face_verification_with_webcam():
    """웹캠 캡처 이미지를 사용하여 추가 얼굴 검증 수행"""
    try:
        # 웹캠 이미지 캡처
        image_path = capture_webcam_image()
        print("[INFO] 2차 검증 시작")
        recognize_faces(image_location=image_path, model="hog")
        print("[INFO] 2차 검증 성공: 얼굴 인증 완료!")
        rotate_servo(90)  # 서보 모터 90도 회전
        time.sleep(1)
        rotate_servo(0)  # 서보 초기화
    except Exception as e:
        fail_exit(f"2차 검증 중 오류 발생: {e}")


# 메인 루프
def loop():
    try:
        print("[INFO] HuskyLens 실행 중... 학습된 얼굴을 기다립니다.")

        while True:
            try:
                print("[DEBUG] HuskyLens 데이터 요청 중...")
                current_data = husky.requestAll()
                print(f"[DEBUG] HuskyLens 데이터 수신 완료: {current_data}")
            except Exception as e:
                fail_exit(f"HuskyLens 데이터 요청 중 오류 발생: {e}")

            # 1차 검증: HuskyLens를 통해 학습된 얼굴 감지
            if detect_face(current_data):
                print("[INFO] 1차 검증 성공: 학습된 얼굴 확인")

                # 2차 검증: USB 웹캠 이미지를 기반으로 수행
                secondary_face_verification_with_webcam()
            else:
                print("[INFO] 대기 중 - 학습된 얼굴 감지되지 않음.")

            time.sleep(0.5)  # 주기 조정

    except KeyboardInterrupt:
        print("[INFO] 프로그램 종료")
        servo.stop()
        GPIO.cleanup()


# 실행
if __name__ == "__main__":
    setup()
    loop()
