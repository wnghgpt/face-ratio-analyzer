"""
자동 데이터 가져오기 스크립트
json_files 폴더를 감시하다가 새 파일이 추가되면 자동으로 데이터베이스에 추가
"""
import time
import json
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from database.db_manager import db_manager


class JSONFileHandler(FileSystemEventHandler):
    """JSON 파일 변경 감지 핸들러"""

    def __init__(self):
        self.processed_files = set()

    def on_created(self, event):
        """새 파일이 생성되었을 때"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # JSON 파일인지 확인
        if file_path.suffix.lower() == '.json':
            print(f"📁 새 JSON 파일 감지: {file_path.name}")

            # 파일이 완전히 쓰여질 때까지 잠시 대기
            time.sleep(1)

            self.import_json_file(file_path)

    def import_json_file(self, file_path):
        """JSON 파일을 데이터베이스로 가져오기"""
        try:
            # 이미 처리된 파일인지 확인
            if str(file_path) in self.processed_files:
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_filename'] = file_path.name

            # 데이터베이스에 추가
            db_manager.import_json_data([data])

            self.processed_files.add(str(file_path))
            print(f"✅ {file_path.name} 데이터베이스에 추가 완료!")

            # 현재 상태 출력
            stats = db_manager.get_stats()
            print(f"📊 현재 데이터베이스: {stats['total_records']}개 레코드")

        except Exception as e:
            print(f"❌ {file_path.name} 처리 실패: {e}")


def start_auto_import(watch_folder="json_files"):
    """자동 가져오기 시작"""

    # 폴더 존재 확인
    if not os.path.exists(watch_folder):
        print(f"❌ 폴더가 없습니다: {watch_folder}")
        print(f"💡 mkdir {watch_folder} 로 폴더를 생성하세요")
        return

    print(f"👀 폴더 감시 시작: {watch_folder}")
    print("🔄 새 JSON 파일이 추가되면 자동으로 데이터베이스에 추가됩니다")
    print("⚠️  종료하려면 Ctrl+C를 누르세요")

    # 기존 파일들 먼저 처리
    handler = JSONFileHandler()
    existing_files = list(Path(watch_folder).glob("*.json"))

    if existing_files:
        print(f"📋 기존 파일 {len(existing_files)}개 확인 중...")
        for file_path in existing_files:
            handler.import_json_file(file_path)

    # 폴더 감시 시작
    observer = Observer()
    observer.schedule(handler, watch_folder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 감시 중단")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    start_auto_import()