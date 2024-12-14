import os
import time
import RPi.GPIO as GPIO
from huskylib import HuskyLensLibrary
from PIL import Image
from detector import recognize_faces

# 전역 변수
husky = None  # HuskyLens 객체
HOME_DIR = os.path.expanduser("~")  # 사용자 홈 디렉토리 경로
SCREENSHOT_DIR = os.path.join(HOME_DIR, "HNUCE", "screenshot")  # 저장 경로
SERVO_PIN = 11  # 서보 모터 GPIO 핀 번호


# 초기 설정 함수
def setup():
    global husky

    # 스크린샷 저장 폴더 생성
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)

    # HuskyLens I2C 연결
    try:
        husky = HuskyLensLibrary("I2C", address=0x32)  # 디폴트 I2C 주소는 0x32
        if husky.knock():
            print("HuskyLens I2C 연결 성공!")
        else:
            print("HuskyLens와의 연결에 실패했습니다. I2C 주소를 확인하세요.")
    except Exception as e:
        print(f"HuskyLens 연결 실패: {e}")

    # GPIO 핀 초기화
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)  # 서보 모터 출력

    # 서보 PWM 설정
    global servo
    servo = GPIO.PWM(SERVO_PIN, 50)  # 서보 모터 50Hz PWM
    servo.start(0)

    print("설정 완료 - 시스템 준비 완료!")


# 서보 모터를 특정 각도로 회전시키는 함수
def rotate_servo(angle):
    duty_cycle = angle / 18.0 + 2
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)


# HuskyLens에서 학습된 얼굴인지 판별 (1차 검증)
def detect_face(data):
    """HuskyLens로부터 받은 데이터를 통해 학습된 사람을 탐지"""
    if not data:
        return False  # 데이터가 없으면 False 반환

    for item in data:
        print(f"검출된 데이터: ID={item.get('ID', 'N/A')}")  # 디버깅용 출력
        if item["ID"] > 0:  # HuskyLens에서 학습된 ID는 1 이상일 것
            return True  # 학습된 얼굴 검출
    return False


# 스크린샷 캡처 기능 (HuskyLens 데이터를 Raspberry Pi에 저장)
def capture_screenshot():
    try:
        # HuskyLens에서 이미지를 읽어옴
        image_data = husky.captureImage()  # 이미지를 읽어오는 메서드 활용 (HuskyLens API 참조)
        if not image_data:
            print("Error: HuskyLens에서 이미지 데이터를 가져오는 데 실패했습니다.")
            return None

        # 캡처된 이미지를 저장할 경로 설정
        screenshot_filename = time.strftime("screenshot_%Y%m%d_%H%M%S.jpg")
        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_filename)

        # 이미지를 저장
        with open(screenshot_path, "wb") as f:
            f.write(image_data)

        print(f"스크린샷이 {screenshot_path}에 저장되었습니다.")
        return screenshot_path
    except Exception as e:
        print(f"스크린샷 저장 실패: {e}")
        return None


# 2차 얼굴 검증 (detector.py 활용)
def secondary_face_verification(screenshot_path):
    try:
        # detector.py의 recognize_faces를 사용해 스크린샷 검증
        print(f"2차 검증 시작: {screenshot_path}")
        recognize_faces(image_location=screenshot_path, model="hog")

        # 2차 검증 성공 시 서보 모터 작동
        print("2차 검증 성공: 얼굴이 확인되었습니다!")
        rotate_servo(90)  # 서보 모터를 90도 회전
        time.sleep(1)
        rotate_servo(0)  # 초기 상태로 복귀
    except Exception as e:
        print(f"2차 검증 중 오류 발생: {e}")


# 메인 로직
def loop():
    try:
        print("HuskyLens 실행 중... 학습된 얼굴 감지를 대기합니다!")

        while True:
            # HuskyLens 데이터 요청
            current_data = None
            try:
                current_data = husky.requestAll()
                print(f"HuskyLens 데이터: {current_data}")  # 디버깅용
            except Exception as e:
                print(f"HuskyLens 데이터 요청 실패: {e}")
                time.sleep(1)
                continue

            # 1차 검증 - 학습된 얼굴 검출 여부
            if detect_face(current_data):
                print("1차 검증 성공: 학습된 얼굴 감지!")

                # 스크린샷 저장
                screenshot_path = capture_screenshot()
                if screenshot_path:
                    print("스크린샷 저장 완료, 2차 검증을 진행합니다.")
                    # 2차 검증 실행
                    secondary_face_verification(screenshot_path)
                else:
                    print("스크린샷 저장 실패, 검증 중단")
            else:
                print("Waiting for trained face detection...")

            # 반복 간격 조정
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("프로그램 종료")
        servo.stop()  # 서보 PWM 정지
        GPIO.cleanup()  # GPIO 초기화


# 실행
if __name__ == "__main__":
    setup()  # 초기 설정
    loop()  # 메인 루프 실행
