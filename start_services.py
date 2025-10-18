#!/usr/bin/env python3
"""
모든 서비스 시작 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from face_db_core import SchemaManager, DatabaseManager

# Initialize db_manager
db_manager = DatabaseManager()

def main():
    """메인 함수"""
    print("🚀 Face Ratio Analyzer 서비스 시작")
    print("=" * 60)

    # 1. 데이터베이스 설정 (개발 모드: 전체 초기화)
    print("1️⃣ 데이터베이스 설정 (개발 모드)...")
    schema_manager = SchemaManager()
    if not schema_manager.reset_database_dev():
        print("❌ 데이터베이스 설정 실패. 종료합니다.")
        return

    print("\n" + "=" * 60)

    # 2. 파일 감시 서비스 시작
    print("2️⃣ 파일 감시 서비스 시작...")
    os.chdir(project_root)  # 프로젝트 루트로 이동

    db_manager.start_file_watcher("source_data/people_json")

if __name__ == "__main__":
    main()