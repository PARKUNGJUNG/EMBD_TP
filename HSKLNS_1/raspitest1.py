import os
import time
import serial
import RPi.GPIO as GPIO
from huskylib import HuskyLensLibrary
from AI.detector import compare_faces, load_image
import lcddriver  # I2C LCD 드라이버 라이브러리

# 전역 변수
husky = None  # HuskyLens 객체
lcd = None  # LCD 객체
PROJECT_DIR = os.getcwd()  # 현재 작업 디렉토리
SCREENSHOT_DIR = os.path.join(PROJECT_DIR, "screenshots")  # 스크린샷 저장 폴더 경로
KNOWN_FACES_DIR = os.path.join(PROJECT_DIR, "known_faces")  # 알려진 얼굴 폴더

BUTTON_PIN = 25  # 버튼 GPIO 핀 번호
SERVO_PIN = 11  # 서보 모터 GPIO 핀 번호


# 초기 설정 함수
def setup():
    global husky, lcd

    # 스크린샷 저장 폴더 생성
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)

    # HuskyLens UART 연결
    try:
        husky_serial = serial.Serial(
            port='/dev/serial0',  # Raspberry Pi의 기본 UART 포트
            baudrate=9600,
            timeout=1
        )
        husky = HuskyLensLibrary(husky_serial)
    except Exception as e:
        print(f"UART 초기화 실패: {e}")
        return

    # HuskyLens 연결 확인
    if husky.knock():
        print("HuskyLens와 성공적으로 연결되었습니다!")
    else:
        print("HuskyLens와의 연결에 실패했습니다.")
        husky = None

    # GPIO 핀 초기화
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 버튼 입력
    GPIO.setup(SERVO_PIN, GPIO.OUT)  # 서보 모터 출력

    # 서보 PWM 설정
    global servo
    servo = GPIO.PWM(SERVO_PIN, 50)  # 서보 모터 50Hz PWM
    servo.start(0)

    # I2C LCD 설정
    lcd = lcddriver.lcd()  # I2C LCD 객체 생성
    lcd.lcd_clear()  # LCD 초기화
    lcd.lcd_display_string("Ready", 1)  # LCD 첫 번째 줄에 출력
    print("설정 완료!")


# 서보 모터를 특정 각도로 회전시키는 함수
def rotate_servo(angle):
    duty_cycle = angle / 18.0 + 2
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)


# 스크린샷 캡처 기능
def capture_screenshot():
    global husky
    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot.jpg")

    try:
        husky.saveScreenshotToSDCard()  # SD 카드에 저장
        time.sleep(2)  # 저장 대기 시간

        # 파일 이동
        source_path = "/sdcard/screenshot.jpg"
        if os.path.exists(source_path):
            os.rename(source_path, screenshot_path)
            print(f"스크린샷이 {screenshot_path}에 저장되었습니다.")
        else:
            print("SD 카드에서 스크린샷을 찾을 수 없습니다.")
        return screenshot_path
    except Exception as e:
        print(f"스크린샷 저장 실패: {e}")
        return None


# 얼굴 검증 로직
def verify_faces(screenshot_path):
    try:
        # LCD에 인증 진행 메시지 출력
        lcd.lcd_clear()
        lcd.lcd_display_string("Authenticating...", 1)  # 인증 진행 알림

        # 저장된 얼굴(known_faces)과 캡처된 스크린샷 비교
        result = compare_faces(KNOWN_FACES_DIR, screenshot_path)

        # 결과 처리
        if result["match_found"]:
            print("검증 성공 - 학습된 얼굴과 일치합니다!")
            lcd.lcd_clear()
            lcd.lcd_display_string("Pass", 1)  # 검증 성공 메시지 출력
            rotate_servo(90)  # 서보 모터 동작
            time.sleep(1)
            rotate_servo(0)  # 초기 상태로 복귀
        else:
            print("검증 실패 - 학습된 얼굴과 일치하지 않습니다!")
            lcd.lcd_clear()
            lcd.lcd_display_string("Denied", 1)  # 검증 실패 메시지 출력
            time.sleep(2)
    except Exception as e:
        print(f"얼굴 검증 중 오류 발생: {e}")
        lcd.lcd_clear()
        lcd.lcd_display_string("Error", 1)  # 오류 메시지 출력


# 메인 로직
def loop():
    try:
        print("버튼을 눌러 시작하세요!")

        while True:
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # 버튼 눌림 확인
                print("버튼 입력 감지 - HuskyLens 검증 시작")
                lcd.lcd_clear()
                lcd.lcd_display_string("Processing...", 1)  # 검증 시작 메시지

                # 1차 HuskyLens 검증
                current_data = husky.requestAll()  # 현재 데이터 요청
                learned_faces = [obj for obj in current_data if obj.learned]  # 학습된 얼굴 필터링

                if learned_faces:
                    print("HuskyLens - 학습된 얼굴 감지됨")

                    # 스크린샷 저장
                    screenshot_path = capture_screenshot()

                    if screenshot_path:
                        print("스크린샷 저장 완료 - 2차 검증 시작")
                        verify_faces(screenshot_path)  # 2차 검증
                    else:
                        print("스크린샷 저장 실패 - 동작 중지")
                else:
                    print("HuskyLens - 학습되지 않은 얼굴 감지됨")
                    lcd.lcd_clear()
                    lcd.lcd_display_string("Denied", 1)  # LCD에 "Denied" 출력
                    time.sleep(2)

                # 버튼 릴리스 대기
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("프로그램 종료")
        servo.stop()  # PWM 정지
        GPIO.cleanup()  # GPIO 초기화
        lcd.lcd_clear()  # LCD 초기화


# 실행
if __name__ == "__main__":
    setup()  # 초기 설정
    loop()  # 메인 루프 실행
