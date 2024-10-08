# EMBD_TP
### 임베디드시스템 학기 프로젝트

## 1331조
20211106 박정웅\
20210511 김형규\
20212434 백종혁

## 필수요소 설치
python **3.9**로 제작되었으며 다른 버전은 에러를 발생시킬 수 있음\
c/c++ 컴파일러 ex) Visual Studio **to install dlib**\
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
├── Gui/\
│   └── gui.py\
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
gui.py 실행\

#### 버튼 설명
train : training 아래 있는 인물별 폴더의 사진을 기반으로 인물을 학습\
validate : 동명의 폴더에 포함된 사진들의 인명 표시\
test : 이미지를 선택하여 학습된 사람의 얼굴인지 확인\
compare : 두 장의 인물사진을 선택해 동일인물인지 비교, 터미널에 정확도 표시 (0에 가까울수록 동일인물일 확률이 증가)