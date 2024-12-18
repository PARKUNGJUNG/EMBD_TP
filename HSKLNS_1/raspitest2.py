import numpy as np
import RPi.GPIO as GPIO
from time import sleep
from detector import load_image, recognize_faces, compare_faces
import cv2

# 경로 지정
WEBCAM_SAVE_PATH = "/home/HNUCE/webcam.jpg"
ENCODINGS_PATH = "/home/HNUCE/output/encodings.pkl"

# 서보모터 GPIO 핀 설정
SERVO_PIN = 18


def setup():
    """
    초기 설정: GPIO 및 서보모터 초기화
    """
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    global pwm
    pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz PWM 주기 설정
    pwm.start(0)
    print("Setup 완료!")


def rotate_servo(angle):
    """
    서보모터를 특정 각도로 회전
    """
    duty = 2 + (angle / 18)
    GPIO.output(SERVO_PIN, True)
    pwm.ChangeDutyCycle(duty)
    sleep(1)
    GPIO.output(SERVO_PIN, False)
    pwm.ChangeDutyCycle(0)


def capture_webcam_image(save_path):
    """
    웹캠 이미지를 캡처하여 지정된 경로에 저장
    """

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("웹캠 열기 실패!")
        return False
    ret, frame = cam.read()
    if not ret:
        print("이미지 캡처 실패!")
        return False
    cv2.imwrite(save_path, frame)
    cam.release()
    print(f"이미지가 {save_path}에 저장되었습니다.")
    return True


def authenticate_user():
    """
    사용자 인증: 얼굴 인식
    """
    print("웹캠 이미지를 캡처합니다...")
    if not capture_webcam_image(WEBCAM_SAVE_PATH):
        return False

    print("녹화된 얼굴을 분석합니다...")
    test_image = load_image(WEBCAM_SAVE_PATH)
    recognized_faces = recognize_faces(test_image, ENCODINGS_PATH)

    if recognized_faces:
        print("인증 성공!")
        return True
    else:
        print("인증 실패!")
        return False


def main_loop():
    """
    메인 루프: 사용자 인증 및 서보모터 제어
    """
    try:
        while True:
            print("사용자 인증을 시작합니다...")
            if authenticate_user():
                print("서보모터 작동 중! 문이 열립니다.")
                rotate_servo(90)  # 문을 열기 위한 서보모터 회전
                sleep(5)  # 문을 열어둔 상태 유지
                rotate_servo(0)  # 문 닫기
            else:
                print("인증 실패. 다시 시도하세요.")
            sleep(2)
    except KeyboardInterrupt:
        print("프로그램 종료 중...")
    finally:
        pwm.stop()
        GPIO.cleanup()
        print("GPIO가 초기화되었습니다.")


if __name__ == "__main__":
    setup()
    main_loop()
