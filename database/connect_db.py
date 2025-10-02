"""
데이터베이스 매니저
"""
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .schema_def import Base, PoolProfile
from .data_handler import crud_service
import hashlib
import json
from datetime import datetime
import os
from .file_watcher import FileWatcherService


class DatabaseManager:
    """
    데이터베이스 연결 관리 및 동기화 담당
    - 데이터베이스 연결 및 세션 관리
    - JSON 파일과 데이터베이스 간 동기화
    - 파일 감시 및 자동 동기화
    """
    def __init__(self, db_url=None):
        # MariaDB 연결
        if db_url is None:
            db_url = "mysql+pymysql://wnghgpt:dnlsehdn@localhost/face_analysis"

        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 데이터베이스 초기화
        self.init_database()

    def init_database(self):
        """데이터베이스 테이블 생성"""
        # 테이블 생성
        Base.metadata.create_all(bind=self.engine)


    @contextmanager
    def get_session(self):
        """세션 컨텍스트 매니저"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


    def import_json_data(self, json_data_list):
        """JSON 데이터를 데이터베이스로 임포트"""
        with self.get_session() as session:
            for json_data in json_data_list:
                try:
                    # 기존 데이터 체크 (이름 기준)
                    existing = session.query(PoolProfile).filter_by(name=json_data.get('name')).first()
                    if existing:
                        continue  # 이미 존재하면 스킵

                    # crud_service 사용
                    crud_service.create_face_data_from_json(session, json_data)

                except Exception as e:
                    print(f"Error importing {json_data.get('name', 'unknown')}: {e}")
                    continue


    def sync_with_folder(self, folder_path="source_data/people_json"):
        """json_files 폴더와 DB 동기화"""
        from pathlib import Path
        import json

        folder_path = Path(folder_path)

        if not folder_path.exists():
            return {"error": "json_files 폴더가 없습니다."}

        # 폴더의 JSON 파일들
        json_files = list(folder_path.glob("*.json"))
        folder_files = set()

        # JSON 파일들 읽기
        valid_json_data = []
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_filename'] = file_path.name
                    name = data.get('name', file_path.stem)
                    folder_files.add(name)
                    valid_json_data.append((name, data))
            except Exception:
                continue

        with self.get_session() as session:
            # DB의 기존 데이터들
            existing_records = session.query(PoolProfile).all()
            db_names = {record.name: record for record in existing_records}

            added_count = 0
            updated_count = 0
            deleted_count = 0

            # 1. 새로운 파일들 추가 & 수정된 파일들 업데이트
            for name, json_data in valid_json_data:
                if name in db_names:
                    # 기존 데이터 업데이트 (태그만)
                    existing_record = db_names[name]

                    # crud_service를 통한 태그 업데이트
                    crud_service.update_face_tags(
                        session,
                        existing_record.id,
                        json_data.get('tags', []),
                        json_data.get('landmarks', [])
                    )
                    updated_count += 1
                else:
                    # 새 데이터 추가 - crud_service 사용
                    crud_service.create_face_data_from_json(session, json_data, name)
                    added_count += 1

            # 2. 폴더에 없는 DB 데이터들 삭제
            for db_name, record in db_names.items():
                if db_name not in folder_files:
                    # crud_service를 통한 데이터 삭제
                    crud_service.delete_face_data(session, record)
                    deleted_count += 1

            session.commit()

            return {
                "added": added_count,
                "updated": updated_count,
                "deleted": deleted_count,
                "total_files": len(folder_files),
                "total_db_records": len(db_names) + added_count - deleted_count
            }

    def start_file_watcher(self, watch_path="source_data/people_json"):
        """파일 감시 서비스 시작"""
        watcher = FileWatcherService(self, watch_path)
        watcher.start()


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()