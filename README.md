# Face Ratio Analyzer

얼굴 비율 분석 데이터를 시각화하고 클러스터링하는 Streamlit 애플리케이션입니다.

## 기능

- JSON 파일에서 얼굴 비율 데이터 자동 로드
- 비율 데이터 2D 산점도 시각화
- K-means 클러스터링
- 클러스터별 통계 분석
- 실시간 파일 변경 감지

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
streamlit run app.py
```

## 데이터 형식

JSON 파일은 다음 형식이어야 합니다:

```json
{
  "name": "photo_001",
  "tags": ["청순한", "동안의"],
  "faceRatio": "1:1.2:0.8",
  "rollAngle": 2.5,
  "ratios": {...}
}
```

## 사용법

1. `json_files/` 폴더에 분석할 JSON 파일들을 복사
2. 브라우저에서 `localhost:8501` 접속
3. 분석 설정 조정 및 시각화 확인