#!/usr/bin/env python3
"""
파일 시스템 실시간 감시 서비스
"""
import os
import sys
import time
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sync_db import DataProcessor

class JSONFileHandler(FileSystemEventHandler):
    """JSON 파일 변경 감지 핸들러"""

    def __init__(self):
        self.processor = DataProcessor()
        print("📁 파일 감시 핸들러 초기화 완료")

    def on_created(self, event):
        """새 파일 생성 시"""
        if event.is_directory:
            return

        if event.src_path.endswith('.json'):
            print(f"🆕 새 JSON 파일 발견: {event.src_path}")
            self._process_file(event.src_path)

    def on_modified(self, event):
        """파일 수정 시"""
        if event.is_directory:
            return

        if event.src_path.endswith('.json'):
            print(f"📝 JSON 파일 수정됨: {event.src_path}")
            self._process_file(event.src_path)

    def _process_file(self, file_path):
        """파일 처리"""
        try:
            # 파일 쓰기가 완료될 때까지 잠시 대기
            time.sleep(0.5)

            # 데이터 처리
            success = self.processor.process_json_file(file_path)

            if success:
                print(f"   ✅ {Path(file_path).name} 처리 완료")
            else:
                print(f"   ❌ {Path(file_path).name} 처리 실패")

        except Exception as e:
            print(f"   ❌ 파일 처리 오류: {e}")

class FileWatcherService:
    """파일 감시 서비스"""

    def __init__(self, watch_path="source_data/people_json"):
        self.watch_path = Path(watch_path)
        self.observer = Observer()
        self.handler = JSONFileHandler()

        # 감시할 디렉토리 확인
        if not self.watch_path.exists():
            print(f"⚠️ 감시할 디렉토리가 없습니다: {self.watch_path}")
            self.watch_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 디렉토리 생성: {self.watch_path}")

    def start(self):
        """서비스 시작"""
        print(f"👁️ 파일 감시 시작: {self.watch_path.absolute()}")

        try:
            self.observer.schedule(
                self.handler,
                str(self.watch_path),
                recursive=False
            )
            self.observer.start()

            print("🚀 파일 감시 서비스 실행 중...")
            print("   - 새 JSON 파일이 추가되면 자동으로 데이터베이스에 저장됩니다")
            print("   - Ctrl+C로 중지할 수 있습니다")

            # 기존 파일들 한 번 처리
            self._process_existing_files()

            # 계속 실행
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n⏹️ 사용자가 서비스를 중지했습니다")
            self.stop()
        except Exception as e:
            print(f"❌ 서비스 오류: {e}")
            self.stop()

    def stop(self):
        """서비스 중지"""
        print("🛑 파일 감시 서비스 중지 중...")
        self.observer.stop()
        self.observer.join()
        print("✅ 서비스 중지 완료")

    def _process_existing_files(self):
        """기존 파일들 처리"""
        print("📋 기존 JSON 파일들 확인 중...")

        json_files = list(self.watch_path.glob("*.json"))

        if not json_files:
            print("   📭 JSON 파일이 없습니다")
            return

        print(f"   📄 {len(json_files)}개 파일 발견")

        for json_file in json_files:
            try:
                success = self.handler.processor.process_json_file(str(json_file))
                if success:
                    print(f"   ✅ {json_file.name}")
                else:
                    print(f"   ⚠️ {json_file.name} (이미 처리됨 또는 오류)")
            except Exception as e:
                print(f"   ❌ {json_file.name}: {e}")

def main():
    """메인 함수"""
    print("🎯 얼굴 데이터 파일 감시 서비스")
    print("=" * 50)

    # 프로젝트 루트로 이동
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # 서비스 시작
    service = FileWatcherService()
    service.start()

if __name__ == "__main__":
    main()