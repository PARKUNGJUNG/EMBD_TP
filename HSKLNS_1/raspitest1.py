import os
import time
import shutil
import sys
import RPi.GPIO as GPIO
from huskylib import HuskyLensLibrary
from detector import recognize_faces

# 전역 변수
husky = None  # HuskyLens 객체
HOME_DIR = os.path.expanduser("~")  # 사용자 홈 디렉토리 경로
SCREENSHOT_DIR = os.path.join(HOME_DIR, "HNUCE", "screenshot")  # 스크린샷 저장 경로
SD_CARD_PATH = "/media/pi/SD_CARD"  # SD 카드가 마운트된 경로 (실환경에 맞게 수정)
SERVO_PIN = 11  # 서보 모터 GPIO 핀 번호


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

    # HuskyLens I2C 연결
    try:
        print("[INFO] HuskyLens I2C 연결 중...")
        husky = HuskyLensLibrary("I2C", address=0x32)  # 디폴트 I2C 주소는 0x32
        if husky.knock():
            print("[INFO] HuskyLens I2C 연결 성공!")
        else:
            fail_exit("HuskyLens 연결 실패: I2C 주소를 확인해주세요.")
    except Exception as e:
        fail_exit(f"HuskyLens 연결 중 오류 발생: {e}")

    # GPIO 초기화
    try:
        print("[INFO] GPIO 설정 중...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SERVO_PIN, GPIO.OUT)

        # 서보 PWM 설정
        global servo
        servo = GPIO.PWM(SERVO_PIN, 50)  # 서보 50Hz PWM 동작
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


# HuskyLens 1차 검증 - 학습된 얼굴인지 확인
def detect_face(data):
    """HuskyLens의 감지 데이터를 분석하여 학습된 얼굴 확인"""
    print("[DEBUG] HuskyLens 데이터 분석 중...")
    if not data:
        print("[DEBUG] 감지 데이터 없음")
        return False

    try:
        for item in data:
            # 객체가 Block 또는 Arrow일 경우 ID 속성 검증
            if hasattr(item, "ID") and item.ID > 0:  # Block 또는 Arrow 객체의 ID 확인
                print(f"[INFO] 학습된 얼굴 감지 - ID: {item.ID}")
                return True  # 학습된 얼굴 있음
        print("[DEBUG] 학습된 얼굴 감지되지 않음")
        return False
    except Exception as e:
        fail_exit(f"HuskyLens 데이터 분석 중 오류 발생: {e}")


# 스크린샷 캡처 기능 (HuskyLens 데이터를 Raspberry Pi에 저장)
def capture_screenshot():
    """HuskyLens SD 카드에 저장된 이미지를 Raspberry Pi로 복사"""
    try:
        print("[DEBUG] HuskyLens 스크린샷 저장 요청 중...")
        if not husky.saveScreenshotToSDCard():
            fail_exit("HuskyLens에서 스크린샷 저장에 실패했습니다.")

        print("[INFO] HuskyLens 스크린샷 SD 카드 저장 완료")

        # SD 카드에 이미지 파일 있는지 확인
        if not os.path.exists(SD_CARD_PATH):
            fail_exit("SD 카드를 찾을 수 없습니다. 연결 상태를 확인하세요.")

        files = [f for f in os.listdir(SD_CARD_PATH) if f.endswith(".jpg")]
        if not files:
            fail_exit("SD 카드에 스크린샷 파일이 없습니다.")

        # 최신 파일 가져오기
        print("[DEBUG] 최신 스크린샷 파일 검색 중...")
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(SD_CARD_PATH, x)))

        # SD 카드에서 Raspberry Pi 저장소로 복사
        source_file = os.path.join(SD_CARD_PATH, latest_file)
        screenshot_filename = time.strftime("screenshot_%Y%m%d_%H%M%S.jpg")
        destination_file = os.path.join(SCREENSHOT_DIR, screenshot_filename)

        shutil.copy(source_file, destination_file)
        print(f"[INFO] 스크린샷 Raspberry Pi 저장 완료: {destination_file}")

        # SD 카드에서 원본 파일 삭제 (선택 사항)
        os.remove(source_file)
        print(f"[INFO] SD 카드에서 원본 파일 삭제 완료: {source_file}")

        return destination_file
    except Exception as e:
        fail_exit(f"스크린샷 처리 중 오류 발생: {e}")


# 2차 검증 (detector.py 활용)
def secondary_face_verification(screenshot_path):
    """detector.py의 recognize_faces를 사용하여 스크린샷 검증"""
    try:
        print(f"[INFO] 2차 검증 시작: {screenshot_path}")
        recognize_faces(image_location=screenshot_path, model="hog")  # 2차 검증
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
            # HuskyLens 데이터 요청
            try:
                print("[DEBUG] HuskyLens 데이터 요청 중...")
                current_data = husky.requestAll()
                print(f"[DEBUG] HuskyLens 데이터 수신 완료: {current_data}")
            except Exception as e:
                fail_exit(f"HuskyLens 데이터 요청 중 오류 발생: {e}")

            # 1차 검증 - 학습된 얼굴 감지
            if detect_face(current_data):
                print("[INFO] 1차 검증 성공: 학습된 얼굴 확인")

                # 스크린샷 저장
                screenshot_path = capture_screenshot()
                if screenshot_path:
                    print("[INFO] 스크린샷 저장 완료, 2차 검증 진행 중...")
                    secondary_face_verification(screenshot_path)  # 2차 검증
                else:
                    print("[WARN] 스크린샷 저장 실패. 2차 검증 건너뜁니다.")
            else:
                print("[INFO] 대기 중 - 학습된 얼굴 감지되지 않음.")

            # 주기 조정
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("[INFO] 프로그램 종료")
        servo.stop()
        GPIO.cleanup()  # GPIO 초기화


# 실행
if __name__ == "__main__":
    setup()
    loop()
