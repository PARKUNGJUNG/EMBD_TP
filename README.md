# EMBD_TP
### 임베디드시스템 학기 프로젝트

## 1331조
20211106 박정웅\
20210511 김형규\
20212434 백종혁

## 필수요소 설치
(venv) $ python -m pip install -r requirements.txt

## 실행방법
### 파일 구조
project/\
│\
├── training/ (학습에 필요한 사진 보관)\
│   ├── person1/ (학습할 사람의 이름)\
│   │   ├── 학습시킬 사진들\
│   │   ├── image1.jpg\
│   │   ├── image2.jpg\
│   │   └── ...\
│   ├── person2/\
│   │   ├── image1.jpg\
│   │   ├── image2.jpg\
│   │   └── ...\
│   └── ...\
├── validation/ (검증할 사진들 순서상관x, CLI에서 경로/이름으로 불러옴)\
│   ├── image1.jpg\
│   ├── image2.jpg\
│   └── ...\
├── output/ (학습시킨 데이터를 인코딩해서 보관)\
│   └── encodings.pkl\
└── AI/\
    └── detector.py

## 실행방법
### CLI
python AI/detector.py --???

usage: detector.py [-h] [--train] [--validate] [--test] [-m {hog,cnn}] [-f F]

Recognize faces in an image

optional arguments:\
  -h, --help  ==   show this help message and exit\
  --train    ==   Train on input data\
  --validate  ==  Validate trained model\
  --test    ==    Test the model with an unknown image\
  -m {hog,cnn} == Which model to use for training: hog (CPU), cnn (GPU)\
  -f F     ==     Path to an image with an unknown face

### GUI
gui.py 실행