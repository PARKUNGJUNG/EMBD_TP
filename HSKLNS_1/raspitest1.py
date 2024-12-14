import os
import time
import RPi.GPIO as GPIO
from huskylib import HuskyLensLibrary
from detector import recognize_faces

# 전역 변수
husky = None  # HuskyLens 객체
HOME_DIR = os.path.expanduser("~")  # 사용자 홈 디렉토리 경로
SCREENSHOT_DIR = os.path.join(HOME_DIR, "HNUCE", "screenshot")  # 스크린샷 저장 경로
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
            print("HuskyLens와의 연결에 실패했습니다. I2C 주소를 확인해주세요.")
    except Exception as e:
        print(f"HuskyLens 연결 실패: {e}")

    # GPIO 초기화
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)

    # 서보 PWM 설정
    global servo
    servo = GPIO.PWM(SERVO_PIN, 50)  # 서보 50Hz PWM 동작
    servo.start(0)

    print("설정 완료 - 시스템 준비 완료!")


# 서보 모터를 특정 각도로 회전시키는 함수
def rotate_servo(angle):
    """서보 모터 회전"""
    duty_cycle = angle / 18.0 + 2
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)


# HuskyLens 1차 검증 - 학습된 얼굴인지 확인
def detect_face(data):
    """HuskyLens의 감지 데이터를 분석하여 학습된 얼굴 확인"""
    if not data:
        return False

    for item in data:
        if item["ID"] > 0:  # 학습된 얼굴이 감지되었을 때
            print(f"학습된 얼굴 감지 - ID: {item['ID']}")
            return True  # 학습된 얼굴 있음
    return False


# 스크린샷 캡처 기능 (HuskyLens 데이터를 Raspberry Pi에 저장)
def capture_screenshot():
    """현재 시점의 HuskyLens 이미지를 캡처하여 파일로 저장"""
    try:
        # 이미지 데이터 수집
        image_data = husky.captureImage()
        if not image_data:
            print("HuskyLens에서 이미지 데이터를 가져오지 못했습니다.")
            return None

        # 캡처된 이미지 저장 경로
        screenshot_filename = time.strftime("screenshot_%Y%m%d_%H%M%S.jpg")
        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_filename)

        # 이미지 저장
        with open(screenshot_path, "wb") as f:
            f.write(image_data)

        print(f"스크린샷 저장 완료: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"스크린샷 저장 실패: {e}")
        return None


# 2차 검증 (detector.py 활용)
def secondary_face_verification(screenshot_path):
    """detector.py의 recognize_faces를 사용하여 스크린샷 검증"""
    try:
        print(f"2차 검증 시작: {screenshot_path}")
        recognize_faces(image_location=screenshot_path, model="hog")  # 2차 검증

        # 2차 검증 성공 시 서보 동작
        print("2차 검증 성공: 얼굴 인증 완료!")
        rotate_servo(90)  # 서보 모터 90도 회전
        time.sleep(1)
        rotate_servo(0)  # 서보 초기화
    except Exception as e:
        print(f"2차 검증 오류 발생: {e}")


# 메인 루프
def loop():
    try:
        print("HuskyLens 실행 중... 학습된 얼굴을 기다립니다.")

        while True:
            # HuskyLens 데이터 요청
            current_data = None
            try:
                current_data = husky.requestAll()
                print(f"HuskyLens 데이터: {current_data}")  # 디버깅용 출력
            except Exception as e:
                print(f"HuskyLens 데이터 요청 실패: {e}")
                time.sleep(1)
                continue

            # 1차 검증 - 학습된 얼굴 감지
            if detect_face(current_data):
                print("1차 검증 성공: 학습된 얼굴 확인")

                # 스크린샷 저장
                screenshot_path = capture_screenshot()
                if screenshot_path:
                    print("스크린샷 저장 완료, 2차 검증 진행 중...")
                    secondary_face_verification(screenshot_path)  # 2차 검증
                else:
                    print("스크린샷 저장 실패. 2차 검증 건너뜁니다.")
            else:
                print("대기 중 - 학습된 얼굴 감지되지 않음.")

            # 주기 조정
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("프로그램 종료")
        servo.stop()
        GPIO.cleanup()  # GPIO 초기화


# 실행
if __name__ == "__main__":
    setup()
    loop()
