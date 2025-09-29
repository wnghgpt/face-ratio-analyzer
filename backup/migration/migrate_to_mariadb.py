#!/usr/bin/env python3
"""
SQLite에서 MariaDB로 데이터 마이그레이션 스크립트
"""
import os
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import create_sqlite_manager, create_mariadb_manager

def backup_sqlite_data():
    """SQLite 데이터 백업"""
    print("📦 SQLite 데이터 백업 중...")

    # SQLite 매니저 생성
    sqlite_manager = create_sqlite_manager("database/face_analytics.db")

    try:
        # 데이터 추출
        data = sqlite_manager.query_data()

        # 백업 파일 생성
        backup_file = "database/sqlite_backup.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        print(f"✅ 백업 완료: {len(data)}개 레코드 → {backup_file}")
        return data

    except Exception as e:
        print(f"❌ SQLite 백업 실패: {e}")
        return []

def test_mariadb_connection():
    """MariaDB 연결 테스트"""
    print("🔗 MariaDB 연결 테스트 중...")

    try:
        mariadb_manager = create_mariadb_manager()

        # 연결 테스트
        from sqlalchemy import text
        with mariadb_manager.get_session() as session:
            result = session.execute(text("SELECT 'Connection OK' as status")).fetchone()
            print(f"✅ MariaDB 연결 성공: {result[0]}")
            return True

    except Exception as e:
        print(f"❌ MariaDB 연결 실패: {e}")
        print("💡 해결 방법:")
        print("   1. MariaDB 서비스 확인: sudo systemctl status mariadb")
        print("   2. 데이터베이스 설정: ./setup_database.sh")
        print("   3. 사용자 권한 확인")
        return False

def migrate_data():
    """데이터 마이그레이션 실행"""
    print("🚚 데이터 마이그레이션 시작...")

    # 1. SQLite 데이터 백업
    sqlite_data = backup_sqlite_data()
    if not sqlite_data:
        print("⚠️ 마이그레이션할 데이터가 없습니다.")
        return False

    # 2. MariaDB 연결 테스트
    if not test_mariadb_connection():
        return False

    # 3. MariaDB에 데이터 마이그레이션
    print("📥 MariaDB로 데이터 이전 중...")
    try:
        mariadb_manager = create_mariadb_manager()

        # JSON 파일에서 데이터 읽기 (기존 방식 활용)
        json_files_path = Path("json_files")
        json_data_list = []

        if json_files_path.exists():
            for file_path in json_files_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        json_data_list.append(json_data)
                except Exception as e:
                    print(f"⚠️ 파일 로딩 오류 ({file_path.name}): {e}")

        # 데이터 임포트
        if json_data_list:
            mariadb_manager.import_json_data(json_data_list)
            print(f"✅ 마이그레이션 완료: {len(json_data_list)}개 파일")
        else:
            print("⚠️ JSON 파일에서 데이터를 찾을 수 없습니다.")

        return True

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        return False

def verify_migration():
    """마이그레이션 검증"""
    print("🔍 마이그레이션 검증 중...")

    try:
        # SQLite 레코드 수
        sqlite_manager = create_sqlite_manager("database/face_analytics.db")
        sqlite_data = sqlite_manager.query_data()
        sqlite_count = len(sqlite_data)

        # MariaDB 레코드 수
        mariadb_manager = create_mariadb_manager()
        mariadb_data = mariadb_manager.query_data()
        mariadb_count = len(mariadb_data)

        print(f"📊 검증 결과:")
        print(f"   SQLite:  {sqlite_count} 레코드")
        print(f"   MariaDB: {mariadb_count} 레코드")

        if mariadb_count >= sqlite_count:
            print("✅ 마이그레이션 검증 성공!")
            return True
        else:
            print("⚠️ 일부 데이터가 누락되었을 수 있습니다.")
            return False

    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🔄 SQLite → MariaDB 마이그레이션")
    print("=" * 50)

    # 작업 디렉토리 확인
    if not os.path.exists("database/face_analytics.db"):
        print("❌ SQLite 데이터베이스 파일을 찾을 수 없습니다.")
        print("   경로: database/face_analytics.db")
        return

    # 마이그레이션 실행
    if migrate_data():
        print("\n🔍 검증 단계...")
        verify_migration()

        print("\n✨ 마이그레이션 완료!")
        print("💡 다음 단계:")
        print("   1. Streamlit 앱 테스트: streamlit run app_advanced.py")
        print("   2. DBeaver에서 연결 확인")
        print("   3. 정상 작동 확인 후 SQLite 파일 백업 보관")
    else:
        print("\n❌ 마이그레이션 실패")
        print("💡 문제 해결 후 다시 시도하세요.")

if __name__ == "__main__":
    main()