# SQLite → MariaDB 마이그레이션 가이드

## 📋 실행 순서

### 1️⃣ MariaDB 설치
```bash
cd "/home/wavus/새 폴더/face-ratio-analyzer"
./mariadb_setup.sh
```

### 2️⃣ MariaDB 보안 설정
```bash
sudo mysql_secure_installation
```
**권장 설정:**
- root 패스워드: 설정 (기억해두세요!)
- 익명 사용자 제거: Y
- 원격 root 로그인 비활성화: Y
- test 데이터베이스 제거: Y
- 권한 테이블 리로드: Y

### 3️⃣ 데이터베이스 및 사용자 생성
```bash
./setup_database.sh
```

### 4️⃣ 데이터 마이그레이션
```bash
cd "/home/wavus/새 폴더/face-ratio-analyzer"
source venv/bin/activate
python migrate_to_mariadb.py
```

### 5️⃣ Streamlit 앱 테스트
```bash
streamlit run app_advanced.py
```

## 🔧 연결 정보

**MariaDB 접속 정보:**
- **Host:** localhost
- **Port:** 3306
- **Database:** face_analytics
- **Username:** face_user
- **Password:** face_password

## 🔍 DBeaver 연결 설정

1. **New Database Connection** 클릭
2. **MySQL** 선택
3. 위 연결 정보 입력
4. **Test Connection** 으로 확인

## ✅ 마이그레이션 검증

### 앱에서 확인:
- 🧮 좌표 분석 탭에서 데이터 로드 확인
- 🔗 태그 연관성 분석 정상 작동 확인
- 🗄️ 데이터베이스 관리 → 폴더-DB 동기화 테스트

### DBeaver에서 확인:
```sql
USE face_analytics;
SHOW TABLES;
SELECT COUNT(*) FROM face_data;
SELECT COUNT(*) FROM tags;
```

## 🚨 문제 해결

### MariaDB 연결 실패:
```bash
# 서비스 상태 확인
sudo systemctl status mariadb

# 서비스 재시작
sudo systemctl restart mariadb

# 로그 확인
sudo journalctl -u mariadb
```

### 권한 오류:
```bash
# MariaDB에 접속하여 권한 재설정
sudo mysql
GRANT ALL PRIVILEGES ON face_analytics.* TO 'face_user'@'localhost';
FLUSH PRIVILEGES;
```

### 포트 충돌:
```bash
# 포트 사용 확인
sudo netstat -tulpn | grep 3306
```

## 🔄 되돌리기 (필요시)

SQLite로 되돌리려면:
```python
# database/db_manager.py 마지막 줄 수정
db_manager = create_sqlite_manager("database/face_analytics.db")
```

## 📂 생성된 파일들

- ✅ `mariadb_setup.sh` - MariaDB 설치 스크립트
- ✅ `create_database.sql` - 데이터베이스 생성 SQL
- ✅ `setup_database.sh` - DB 설정 스크립트
- ✅ `migrate_to_mariadb.py` - 마이그레이션 스크립트
- ✅ `database/sqlite_backup.json` - SQLite 백업 (마이그레이션 후 생성)
- ✅ `requirements.txt` - PyMySQL 추가됨
- ✅ `database/db_manager.py` - MariaDB 지원 추가

## 🎯 마이그레이션 완료 후 장점

1. **동시 접근**: Streamlit + DBeaver 동시 사용 가능
2. **WSL2 호환**: 파일 잠금 문제 해결
3. **성능 향상**: 대용량 데이터에서 더 빠름
4. **확장성**: 다중 사용자, 원격 접근 지원
5. **표준화**: 표준 SQL, 더 많은 도구 지원

## 🆘 지원

문제 발생 시:
1. 위 문제 해결 섹션 확인
2. 로그 파일 확인: `sudo journalctl -u mariadb`
3. MariaDB 공식 문서 참조