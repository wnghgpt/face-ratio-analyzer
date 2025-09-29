#!/bin/bash
# MariaDB 데이터베이스 및 사용자 설정 스크립트

echo "🗄️ MariaDB 데이터베이스 설정 시작..."

# MariaDB 서비스 상태 확인
if ! systemctl is-active --quiet mariadb; then
    echo "❌ MariaDB 서비스가 실행되지 않았습니다."
    echo "   다음 명령어로 서비스를 시작하세요: sudo systemctl start mariadb"
    exit 1
fi

echo "✅ MariaDB 서비스 실행 중"

# 데이터베이스 및 사용자 생성
echo "📝 데이터베이스 및 사용자 생성 중..."
sudo mysql < create_database.sql

if [ $? -eq 0 ]; then
    echo "✅ 데이터베이스 설정 완료!"
    echo ""
    echo "📋 연결 정보:"
    echo "   - Database: face_analytics"
    echo "   - User: face_user"
    echo "   - Password: face_password"
    echo "   - Host: localhost"
    echo "   - Port: 3306"
    echo ""
    echo "🔗 연결 테스트:"
    mysql -u face_user -pface_password -e "USE face_analytics; SELECT 'Connection OK' as status;"
else
    echo "❌ 데이터베이스 설정 중 오류 발생"
    exit 1
fi