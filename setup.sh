#!/bin/bash

# Face Ratio Analyzer 설정 스크립트

echo "🔧 Face Ratio Analyzer 설정을 시작합니다..."

# 가상환경 생성
echo "📦 가상환경을 생성하는 중..."
python3 -m venv venv

# 가상환경 활성화
echo "⚡ 가상환경을 활성화하는 중..."
source venv/bin/activate

# 패키지 업그레이드
echo "📈 pip를 업그레이드하는 중..."
pip install --upgrade pip

# 의존성 패키지 설치
echo "📚 패키지를 설치하는 중..."
pip install -r requirements.txt

echo "✅ 설정이 완료되었습니다!"
echo ""
echo "🚀 사용 방법:"
echo "1. 가상환경 활성화: source venv/bin/activate"
echo "2. JSON 파일을 json_files/ 폴더에 복사"
echo "3. 앱 실행: streamlit run app.py"
echo "4. 브라우저에서 localhost:8501 접속"
echo ""
echo "💡 가상환경 비활성화: deactivate"