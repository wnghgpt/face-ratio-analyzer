#!/usr/bin/env python3
"""
현재 사용 중인 데이터베이스 확인 스크립트
"""
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def check_current_database():
    """현재 사용 중인 데이터베이스 확인"""
    print("🔍 현재 데이터베이스 연결 정보 확인")
    print("=" * 50)

    try:
        # 연결 URL 확인
        print(f"📋 연결 URL: {db_manager.db_url}")

        # DB 타입 확인
        if db_manager.db_url.startswith('sqlite'):
            print("🗄️ 데이터베이스 타입: SQLite")
            db_file = db_manager.db_url.replace('sqlite:///', '')
            print(f"📁 파일 경로: {db_file}")

            # 파일 존재 확인
            if os.path.exists(db_file):
                file_size = os.path.getsize(db_file)
                print(f"📏 파일 크기: {file_size:,} bytes")
            else:
                print("⚠️ SQLite 파일이 존재하지 않습니다!")

        elif db_manager.db_url.startswith('mysql'):
            print("🐬 데이터베이스 타입: MySQL/MariaDB")

        # 실제 연결 테스트
        print("\n🔗 연결 테스트 중...")
        from sqlalchemy import text

        with db_manager.get_session() as session:
            # DB 정보 쿼리
            if db_manager.db_url.startswith('sqlite'):
                result = session.execute(text("SELECT sqlite_version() as version")).fetchone()
                print(f"✅ SQLite 버전: {result[0]}")

                # 테이블 목록
                tables_result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
                tables = [row[0] for row in tables_result]

            else:  # MySQL/MariaDB
                result = session.execute(text("SELECT VERSION() as version")).fetchone()
                print(f"✅ MariaDB/MySQL 버전: {result[0]}")

                # 현재 데이터베이스
                db_result = session.execute(text("SELECT DATABASE() as current_db")).fetchone()
                print(f"📊 현재 데이터베이스: {db_result[0]}")

                # 테이블 목록
                tables_result = session.execute(text("SHOW TABLES")).fetchall()
                tables = [row[0] for row in tables_result]

            print(f"\n📋 테이블 목록 ({len(tables)}개):")
            for table in tables:
                print(f"   - {table}")

            # 데이터 개수 확인
            if 'face_data' in tables:
                count_result = session.execute(text("SELECT COUNT(*) FROM face_data")).fetchone()
                print(f"\n📊 face_data 테이블: {count_result[0]}개 레코드")

        print("\n✅ 데이터베이스 연결 및 확인 완료!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("\n🔧 문제 해결:")
        print("   1. MariaDB 서비스 상태: sudo systemctl status mariadb")
        print("   2. SQLite 파일 확인: ls -la database/")

if __name__ == "__main__":
    check_current_database()