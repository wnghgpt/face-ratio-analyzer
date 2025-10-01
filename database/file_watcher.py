"""
파일 감시 서비스
"""
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class JSONFileHandler(FileSystemEventHandler):
    """JSON 파일 변경 감지 핸들러"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
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

            # 폴더 동기화 실행 (단일 파일도 폴더 동기화로 처리)
            folder_path = str(Path(file_path).parent)
            result = self.db_manager.sync_with_folder(folder_path)

            if result and (result.get('added', 0) > 0 or result.get('updated', 0) > 0):
                print(f"   ✅ {Path(file_path).name} 처리 완료")
            else:
                print(f"   ⚠️ {Path(file_path).name} 변경사항 없음")

        except Exception as e:
            print(f"   ❌ 파일 처리 오류: {e}")


class FileWatcherService:
    """파일 감시 서비스"""

    def __init__(self, db_manager, watch_path="source_data/people_json"):
        self.db_manager = db_manager
        self.watch_path = Path(watch_path)
        self.observer = Observer()
        self.handler = JSONFileHandler(db_manager)

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

            print("🔄 파일 감시 서비스가 시작되었습니다.")
            print("   - 새 JSON 파일 추가 시 자동 DB 동기화")
            print("   - 기존 JSON 파일 수정 시 자동 업데이트")
            print("   - Ctrl+C로 종료")

            # 무한 대기
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()

        except Exception as e:
            print(f"❌ 파일 감시 시작 실패: {e}")

    def stop(self):
        """서비스 중지"""
        print("\n🛑 파일 감시 서비스 중지 중...")
        self.observer.stop()
        self.observer.join()
        print("✅ 파일 감시 서비스가 중지되었습니다.")