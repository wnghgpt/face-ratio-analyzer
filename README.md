# Face Ratio Analyzer 🎭

얼굴 비율 분석을 위한 완전한 데이터 분석 플랫폼입니다. 복잡한 얼굴 비율 데이터를 쉽게 시각화하고 분석할 수 있습니다.

## ✨ 주요 기능

### 📊 다양한 분석 도구

**기존 비율 분석 (Tab 1)**
- **산점도 (Scatter Plot)** - 두 변수 간의 관계 분석
- **히스토그램** - 단일 변수의 분포 시각화
- **박스플롯** - 사분위수와 이상치 탐지
- **바이올린 플롯** - 분포 모양 상세 분석
- **PCA 분석** - 고차원 데이터 차원 축소
- **클러스터링** - K-means를 통한 자동 그룹화
- **PCA + 클러스터링** - 차원축소 후 클러스터링

**🆕 실시간 좌표 분석 (Tab 2)**
- **동적 점 선택** - 492개 랜드마크에서 원하는 점들 선택
- **거리 계산** - 유클리드, 맨하탄, X/Y/Z 개별 거리
- **기하학적 계산** - 삼각형 넓이, 각도, 다각형 넓이
- **실시간 통계** - 평균, 표준편차, 분산 등 즉시 계산

### 🎯 스마트 데이터 처리
- JSON 파일 자동 import 및 데이터베이스 저장
- 복잡한 비율 구조 자동 파싱 (`1:1.2:0.8` 형식 지원)
- 태그별 데이터 필터링 및 그룹화
- 실시간 파일 감시 (`auto_import.py`)

### 🔧 사용자 친화적 인터페이스
- 직관적인 비율 종류 선택
- 동적 변수 선택 시스템
- 실시간 통계 정보 표시

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 저장소 클론
git clone https://github.com/wnghgpt/face-ratio-analyzer
cd face-ratio-analyzer

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 앱 실행
```bash
# 🆕 고급 버전 (비율 분석 + 좌표 분석) (추천)
streamlit run app_advanced.py

# 또는 기존 메인 분석 도구
streamlit run app_enhanced.py

# 또는 간단한 버전
streamlit run app_simple.py
```

### 3. 자동 데이터 import (선택사항)
```bash
# 파일 변경 감시 시작
python auto_import.py
```

## 📁 프로젝트 구조

```
face-ratio-analyzer/
├── app_advanced.py     # 🆕 고급 분석 앱 (비율 + 좌표 분석)
├── app_enhanced.py     # 메인 분석 앱 (기존 비율 분석)
├── app_simple.py       # 간단한 분석 앱
├── auto_import.py      # 자동 파일 import
├── database/           # 데이터베이스 관련
│   ├── db_manager.py   # 데이터베이스 매니저
│   ├── models.py       # SQLAlchemy 모델
│   └── face_analytics.db
├── engines/            # 분석 엔진
│   ├── ratio_parser.py # 비율 파싱 엔진
│   └── analysis_engine.py
├── json_files/         # 샘플 데이터
│   ├── sample_001.json
│   └── ...
└── requirements.txt    # 의존성 목록
```

## 📋 데이터 형식

JSON 파일은 다음 형식을 지원합니다:

### 기본 형식
```json
{
  "name": "샘플_001",
  "tags": ["귀여운", "밝은"],
  "faceRatio": "1:1.2:0.8",
  "rollAngle": 2.5
}
```

### 상세 비율 정보 (권장)
```json
{
  "name": "샘플_001",
  "tags": ["귀여운", "밝은"],
  "faceRatio": "1:1.2:0.8",
  "rollAngle": 2.5,
  "ratios": {
    "전체비율": {
      "얼굴길이 비율": "1:1.2:0.8",
      "얼굴 가로세로 비율": "1:0.75"
    },
    "항목별": {
      "눈": {
        "눈너비:미간": {
          "value": "0.2:0.22:0.25:0.21:0.18",
          "hasLeftRight": false
        }
      }
    }
  }
}
```

### 🆕 좌표 데이터 형식 (실시간 계산용)
```json
{
  "name": "miyun",
  "tags": ["고양이", "이국적인", "여성스런"],
  "landmarks": [
    {"mpidx": 0, "x": 0.495, "y": 0.633, "z": 0.0},
    {"mpidx": 1, "x": 0.502, "y": 0.571, "z": -0.1},
    {"mpidx": 33, "x": 0.385, "y": 0.465, "z": -0.05},
    {"mpidx": 133, "x": 0.615, "y": 0.465, "z": -0.05},
    // ... 492개 점 총
  ]
}
```

## 💡 사용 팁

### 분석 도구 선택 가이드

**기존 비율 분석 (Tab 1)**
- **단일 변수 분석** → 히스토그램, 박스플롯, 바이올린 플롯
- **두 변수 관계** → 산점도
- **전체 패턴 파악** → PCA 분석
- **자동 그룹화** → 클러스터링
- **종합 분석** → PCA + 클러스터링

**🆕 좌표 분석 (Tab 2)**
- **눈 간격 분석** → 점 2개 (mpidx 33, 133) + 유클리드 거리
- **코 대칭성** → 점 3개 (mpidx 1, 31, 35) + 삼각형 넓이
- **얼굴 너비** → 점 2개 (mpidx 234, 454) + X 거리
- **입술 두께** → 점 2개 (mpidx 13, 14) + Y 거리
- **3D 깊이 분석** → 점 1개 + Z 좌표 또는 원점 거리

### 데이터 준비
1. `json_files/` 폴더에 JSON 파일 추가
2. 앱에서 "🔄 데이터 새로고침" 버튼 클릭
3. 또는 `auto_import.py` 실행으로 자동 감시

## 🛠 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python 3.12+
- **Database**: SQLite + SQLAlchemy ORM
- **분석**: Pandas, NumPy, Scikit-learn
- **시각화**: Plotly
- **파일 감시**: Watchdog

## 📝 라이센스

MIT License