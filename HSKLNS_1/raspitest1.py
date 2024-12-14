import os
import time
import serial
import RPi.GPIO as GPIO
from huskylib import HuskyLensLibrary
from PIL import Image

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

    # HuskyLens UART 연결
    try:
        # I2C 방식으로 HuskyLens 라이브러리 초기화
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


# 얼굴 검증 로직
def verify_faces(screenshot_path):
    try:
        # 올바른 경로로 저장된 스크린샷 파일이 있는지 확인
        if not os.path.exists(screenshot_path):
            print("Error: 스크린샷 파일을 찾을 수 없습니다.")
            return

        # 얼굴 검증 작업 (compare_faces 함수 사용 가정)
        result = compare_faces(KNOWN_FACES_DIR, screenshot_path)

        # 검증 결과 처리
        if result["match_found"]:
            print("검증 성공 - 학습된 얼굴과 일치합니다!")
            rotate_servo(90)  # 서보 모터 동작
            time.sleep(1)
            rotate_servo(0)  # 초기 상태로 복귀
        else:
            print("검증 실패 - 학습된 얼굴과 일치하지 않습니다!")
    except Exception as e:
        print(f"verify_faces 오류 발생: {e}")


# 학습된 사람 데이터 감지 함수
def detect_trained_people(data):
    """데이터에서 학습된 사람을 탐지"""
    if not data:
        return False  # 데이터가 없으면 False 반환

    for item in data:
        print(f"검출된 데이터: ID={item.get('ID', 'N/A')}")  # 디버깅용 출력
        if item["ID"] > 0:  # 학습된 ID는 0 이상의 값 (HuskyLens 문서 참고)
            return item  # 학습된 데이터를 반환
    return False


# 메인 로직
def loop():
    try:
        print("HuskyLens 실행 중... 학습된 얼굴 감지를 기다립니다!")

        while True:
            # HuskyLens로부터 데이터 요청 (폴링)
            try:
                current_data = husky.requestAll()  # 현재 데이터를 가져옴
                print(f"현재 데이터: {current_data}")  # 디버깅용 로그 출력
            except Exception as e:
                print("HuskyLens에서 데이터를 가져오는 데 실패했습니다.")
                time.sleep(1)
                continue

            # 학습된 얼굴 데이터 확인
            trained_face = detect_trained_people(current_data)

            if trained_face:
                print(f"HuskyLens - 학습된 얼굴 감지: ID={trained_face['ID']}")

                # 스크린샷 저장
                screenshot_path = capture_screenshot()

                if screenshot_path:
                    print("스크린샷 저장 완료 - 얼굴 검증 중")
                    verify_faces(screenshot_path)  # 저장된 얼굴로 검증
                else:
                    print("스크린샷 저장 실패 - 동작 중지")
            else:
                # 학습된 데이터가 없으면 대기
                print("Waiting for trained face detection...")

            time.sleep(0.5)  # 폴링 간격 조정
    except KeyboardInterrupt:
        print("프로그램 종료")
        servo.stop()  # PWM 정지
        GPIO.cleanup()  # GPIO 초기화


# 실행
if __name__ == "__main__":
    setup()  # 초기 설정
    loop()  # 메인 루프 실행
