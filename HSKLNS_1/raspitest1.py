import os
import time
import RPi.GPIO as GPIO
from huskylib import HuskyLensLibrary

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
        # HuskyLensLibrary를 I2C로 초기화
        husky = HuskyLensLibrary("I2C", '', address=0x32)  # 기본 I2C 주소: 0x32
        if husky.knock():
            print("HuskyLens 연결 성공 (I2C)!")
        else:
            print("HuskyLens와의 연결에 실패했습니다.")
    except Exception as e:
        print(f"HuskyLens(I2C) 연결 실패: {e}")
        return

    # GPIO 핀 초기화
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)  # 서보 모터 출력

    # 서보 PWM 설정
    global servo
    servo = GPIO.PWM(SERVO_PIN, 50)  # 서보 모터 50Hz PWM
    servo.start(0)

    print("초기 설정 완료 - 시스템 준비!")


# 서보 모터를 특정 각도로 회전시키는 함수
def rotate_servo(angle):
    """
    서보 모터를 특정 각도로 회전
    """
    duty_cycle = angle / 18.0 + 2
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)


# 학습된 사람 데이터 감지 함수
def detect_trained_people(data):
    """
    HuskyLens 데이터에서 학습된 사람 객체(ID가 있는 데이터)를 감지
    """
    if not data:
        return False  # HuskyLens에서 데이터가 없으면 False 반환

    for item in data:
        # 현재 검출된 데이터 정보 출력 (디버깅용)
        print(f"검출된 데이터: ID={item.get('ID', 'N/A')}")
        if item["ID"] > 0:  # ID가 0보다 크면 학습된 데이터로 판정
            return item  # 학습된 사람 데이터 반환
    return False


# 메인 루프 실행
def loop():
    try:
        print("HuskyLens 실행 중... 학습된 얼굴 감지 대기!")

        while True:
            try:
                # HuskyLens 데이터 요청
                current_data = husky.requestAll()
                # 현재 데이터를 출력 (디버깅용)
                print(f"현재 데이터: {current_data}")
            except Exception as e:
                print(f"HuskyLens에서 데이터를 가져오는 데 실패했습니다: {e}")
                time.sleep(1)
                continue

            # 학습된 얼굴 데이터 감지
            trained_face = detect_trained_people(current_data)

            if trained_face:
                print(f"HuskyLens - 학습된 사람 감지: ID={trained_face['ID']}")
                # 학습된 인물이 감지되었을 경우 서보 모터 동작 (예: 문 열기)
                rotate_servo(90)  # 서보 모터 90도 회전
                time.sleep(1)
                rotate_servo(0)  # 서보 모터 0도로 복귀
            else:
                print("HuskyLens 대기 중... 학습된 얼굴 감지 없음.")

            time.sleep(0.5)  # 폴링 간격
    except KeyboardInterrupt:
        print("프로그램 종료")
        servo.stop()  # PWM 정지
        GPIO.cleanup()  # GPIO 초기화


# 실행
if __name__ == "__main__":
    setup()  # 초기 설정
    loop()  # 메인 루프 실행
