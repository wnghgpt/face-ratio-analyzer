# Face Ratio Analyzer - 배포 가이드

## 📋 시스템 개요

Face Ratio Analyzer는 얼굴 비율 데이터를 분석하는 웹 애플리케이션입니다. Streamlit을 기반으로 구축되었으며, 데이터베이스 기반의 동적 분석 엔진을 제공합니다.

## 🏗️ 아키텍처

### 핵심 컴포넌트

1. **데이터베이스 레이어** (`database/`)
   - `models.py`: SQLAlchemy 데이터베이스 모델
   - `db_manager.py`: 데이터베이스 관리 및 세션 처리

2. **분석 엔진** (`engines/`)
   - `ratio_parser.py`: 다양한 비율 형식 파싱
   - `analysis_engine.py`: 동적 분석 파이프라인

3. **UI 컴포넌트** (`components/`)
   - `data_selector.py`: 데이터 필터링 및 선택
   - `variable_selector.py`: 분석 변수 선택
   - `analysis_builder.py`: 분석 설정 구성
   - `results_viewer.py`: 결과 시각화

4. **메인 애플리케이션**
   - `app.py`: Streamlit 웹 애플리케이션

## 🚀 설치 및 실행

### 1. 요구사항

```bash
Python 3.8 이상
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 애플리케이션 실행

```bash
streamlit run app.py
```

## 📂 디렉토리 구조

```
face-ratio-analyzer/
├── app.py                          # 메인 애플리케이션
├── requirements.txt                 # 의존성 패키지
├── DEPLOYMENT.md                   # 배포 가이드
├── test_imports.py                 # 시스템 테스트
├── database/
│   ├── __init__.py
│   ├── models.py                   # 데이터베이스 모델
│   ├── db_manager.py              # 데이터베이스 관리자
│   └── face_analytics.db          # SQLite 데이터베이스 (자동 생성)
├── engines/
│   ├── __init__.py
│   ├── ratio_parser.py            # 비율 파싱 엔진
│   └── analysis_engine.py         # 동적 분석 엔진
├── components/
│   ├── __init__.py
│   ├── data_selector.py           # 데이터 선택 UI
│   ├── variable_selector.py       # 변수 선택 UI
│   ├── analysis_builder.py        # 분석 설정 UI
│   └── results_viewer.py          # 결과 표시 UI
└── json_files/                    # JSON 데이터 파일 (사용자 생성)
```

## 📊 데이터 형식

### 지원하는 JSON 형식

```json
{
  "name": "sample_001",
  "tags": ["태그1", "태그2"],
  "faceRatio": "1:1.2:0.8",
  "rollAngle": 2.5,
  "ratios": {
    "detail": "추가 비율 정보"
  }
}
```

### 지원하는 비율 형식

- `1:x:y` (정규화된 3차원)
- `1:x` (정규화된 2차원)
- `x:y` (직접 2차원)
- `x:y:z:w` (직접 4차원)
- `x:y:z:w:v` (직접 5차원)

## 🔧 기능 설명

### 1. 데이터 가져오기
- JSON 파일 폴더에서 일괄 import
- CSV 파일 업로드 (구현 예정)
- 자동 비율 파싱 및 데이터베이스 저장

### 2. 동적 분석
- **태그 기반 필터링**: "귀여운&섹시한" 등 복합 조건
- **변수 자동 추천**: 분석 목적에 따른 변수 조합 제안
- **분석 파이프라인**: PCA, t-SNE, UMAP, K-means, DBSCAN 등
- **실시간 시각화**: Plotly 기반 인터랙티브 차트

### 3. 분석 템플릿
- **기본 PCA 분석**: 얼굴 비율의 주성분 분석
- **클러스터링 분석**: K-means 기반 그룹 분석
- **PCA + 클러스터링**: 차원축소 후 클러스터링

### 4. 설정 관리
- 분석 설정 저장/불러오기
- 캐시 기반 결과 저장
- 사용 통계 추적

## 🛠️ 시스템 테스트

```bash
python3 test_imports.py
```

테스트 항목:
- ✅ 파일 구조 검증
- ✅ 비율 파싱 로직
- ⚠️ 모듈 import (패키지 설치 필요)

## 📈 사용 예시

### 1. 데이터 가져오기
1. `json_files/` 폴더에 JSON 파일들 배치
2. "📥 데이터 가져오기" 메뉴에서 "폴더 스캔"
3. "데이터베이스로 가져오기" 실행

### 2. 분석 실행
1. "🔍 데이터 분석" 메뉴 선택
2. 단계별 분석:
   - 데이터 선택 (태그 필터 등)
   - 변수 선택 (X, Y축 등)
   - 분석 설정 (PCA, 클러스터링 등)
   - 결과 확인

### 3. 빠른 분석
"📊 대시보드" 메뉴에서 원클릭 분석:
- 기본 PCA 분석
- 클러스터링 분석
- PCA + 클러스터링

## 🚨 문제 해결

### 1. 패키지 설치 오류
```bash
# 가상환경 생성 권장
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 2. 데이터베이스 오류
```bash
# 데이터베이스 파일 삭제 후 재생성
rm database/face_analytics.db
```

### 3. 메모리 부족
- 대용량 데이터셋의 경우 배치 처리 구현 필요
- 차원축소 전 데이터 샘플링 권장

## 🔄 업데이트 계획

### 단기 (1-2주)
- [ ] CSV 가져오기 기능 완성
- [ ] 데이터 정리 및 중복 제거
- [ ] 추가 시각화 타입

### 중기 (1-2개월)
- [ ] 웹 기반 JSON 업로드
- [ ] 분석 결과 리포트 생성
- [ ] 사용자 권한 관리

### 장기 (3개월+)
- [ ] 실시간 분석 API
- [ ] 머신러닝 모델 통합
- [ ] 클라우드 배포

## 📞 지원

문제가 발생하거나 기능 요청이 있으시면:
1. GitHub Issues에 등록
2. 로그 파일과 함께 상세한 설명 제공
3. 재현 가능한 최소 예제 포함

---

**버전**: 1.0.0
**최종 업데이트**: 2024년 12월
**호환성**: Python 3.8+, Streamlit 1.35+