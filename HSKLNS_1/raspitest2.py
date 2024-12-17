import cv2
import pickle
import numpy as np
from face_recognition import face_locations, face_encodings, compare_faces
from collections import Counter

# 설정
ENCODINGS_PATH = "output/encodings.pkl"


def load_encodings(encodings_path):
    """학습된 얼굴 데이터 로드"""
    try:
        with open(encodings_path, 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        print("[ERROR] 인코딩 파일을 찾을 수 없습니다. 학습 데이터를 생성하세요.")
        return None


def recognize_face_from_webcam():
    """웹캠 기반 얼굴 검출 및 인식"""
    # 기존 학습된 인코딩 로드
    data = load_encodings(ENCODINGS_PATH)
    if data is None:
        return

    # 웹캠 열기
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print("[ERROR] 웹캠을 열 수 없습니다. 연결 상태를 확인하세요.")
        return

    print("[INFO] 웹캠 작동 중. ESC 키를 눌러 종료합니다.")

    while True:
        # 프레임 읽기
        ret, frame = video_capture.read()
        if not ret:
            print("[ERROR] 프레임을 읽을 수 없습니다.")
            break

        # 얼굴 검출 및 인코딩
        rgb_frame = frame[:, :, ::-1]  # OpenCV의 BGR -> RGB
        face_locations_list = face_locations(rgb_frame)
        face_encodings_list = face_encodings(rgb_frame, face_locations_list)

        # 얼굴 인식 결과
        for face_encoding, face_location in zip(face_encodings_list, face_locations_list):
            matches = compare_faces(data['encodings'], face_encoding)
            votes = Counter(name for match, name in zip(matches, data['names']) if match)
            recognized_name = votes.most_common(1)[0][0] if votes else "Unknown"

            # 얼굴 위치 및 이름 표시
            top, right, bottom, left = face_location
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, recognized_name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 화면에 출력
        cv2.imshow('Face Recognition', frame)

        # ESC를 누르면 루프 종료
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # 리소스 정리
    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    recognize_face_from_webcam()
