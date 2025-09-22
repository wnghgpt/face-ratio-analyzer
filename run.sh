#!/bin/bash

# Face Ratio Analyzer 실행 스크립트

echo "🚀 Face Ratio Analyzer를 시작합니다..."

# 가상환경 활성화 확인
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다. 먼저 setup.sh를 실행해주세요."
    echo "   실행 방법: ./setup.sh"
    exit 1
fi

# 가상환경 활성화
echo "⚡ 가상환경을 활성화합니다..."
source venv/bin/activate

# JSON 파일 확인
if [ ! "$(ls -A json_files/*.json 2>/dev/null)" ]; then
    echo "⚠️  json_files/ 폴더에 JSON 파일이 없습니다."
    echo "💡 분석할 JSON 파일들을 json_files/ 폴더에 복사해주세요."
    echo ""
fi

echo "🌐 Streamlit 앱을 실행합니다..."
echo "📱 브라우저에서 http://localhost:8501 을 열어주세요."
echo ""

# Streamlit 실행
streamlit run app.py