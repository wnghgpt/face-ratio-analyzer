#!/bin/bash
# MariaDB 설치 및 설정 스크립트

echo "🚀 MariaDB 설치 시작..."

# 1. 패키지 업데이트
sudo apt update

# 2. MariaDB 설치
sudo apt install -y mariadb-server mariadb-client

# 3. MariaDB 서비스 시작 및 활성화
sudo systemctl start mariadb
sudo systemctl enable mariadb

# 4. MariaDB 상태 확인
sudo systemctl status mariadb

echo "✅ MariaDB 설치 완료!"
echo "📝 다음 단계: sudo mysql_secure_installation 실행"
echo "   - root 패스워드 설정"
echo "   - 불필요한 계정 제거"
echo "   - 원격 root 로그인 비활성화"
echo "   - 테스트 DB 제거"