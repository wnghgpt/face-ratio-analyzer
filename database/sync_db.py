#!/usr/bin/env python3
"""
JSON 파일 데이터 처리 서비스
"""
import os
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connect_db import db_manager
from database.schema_def import FaceData, Landmark

class DataProcessor:
    """JSON 파일 데이터 처리"""

    def __init__(self):
        print("⚙️ 데이터 처리기 초기화 완료")

    def process_json_file(self, file_path):
        """JSON 파일 처리하여 데이터베이스에 저장"""
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"❌ 파일이 존재하지 않습니다: {file_path}")
            return False

        try:
            # JSON 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 파일명에서 이름 추출
            face_name = file_path.stem

            with db_manager.get_session() as session:
                # 중복 확인
                existing = session.query(FaceData).filter_by(name=face_name).first()
                if existing:
                    # 이미 존재하면 업데이트
                    return self._update_face_data(session, existing, data, str(file_path))
                else:
                    # 새로 생성
                    return self._create_face_data(session, face_name, data, str(file_path))

        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            return False
        except Exception as e:
            print(f"❌ 파일 처리 오류: {e}")
            return False

    def _create_face_data(self, session, face_name, data, file_path):
        """새 얼굴 데이터 생성"""
        try:
            # FaceData 생성
            face_data = FaceData(
                name=face_name,
                file_path=file_path,
                face_ratio_raw=data.get('face_ratio_raw'),
                ratio_1=data.get('ratio_1'),
                ratio_2=data.get('ratio_2'),
                ratio_3=data.get('ratio_3'),
                ratio_4=data.get('ratio_4'),
                ratio_5=data.get('ratio_5'),
                ratio_2_1=data.get('ratio_2_1'),
                ratio_3_1=data.get('ratio_3_1'),
                ratio_3_2=data.get('ratio_3_2'),
                roll_angle=data.get('roll_angle'),
                ratios_detail=json.dumps(data.get('ratios_detail', {})),
                landmarks=json.dumps(data.get('landmarks', [])),
                meta_data=json.dumps(data.get('metadata', {}))
            )

            session.add(face_data)
            session.flush()  # ID 생성을 위해

            # 랜드마크 데이터 처리
            landmarks_added = self._process_landmarks(session, face_data.id, data.get('landmarks', []))

            session.commit()

            print(f"   🆕 새 얼굴 데이터 생성: {face_name}")
            print(f"      - 랜드마크: {landmarks_added}개")

            return True

        except Exception as e:
            session.rollback()
            print(f"❌ 얼굴 데이터 생성 실패: {e}")
            return False

    def _update_face_data(self, session, existing_face, data, file_path):
        """기존 얼굴 데이터 업데이트"""
        try:
            # 기본 데이터 업데이트
            existing_face.file_path = file_path
            existing_face.face_ratio_raw = data.get('face_ratio_raw')
            existing_face.ratio_1 = data.get('ratio_1')
            existing_face.ratio_2 = data.get('ratio_2')
            existing_face.ratio_3 = data.get('ratio_3')
            existing_face.ratio_4 = data.get('ratio_4')
            existing_face.ratio_5 = data.get('ratio_5')
            existing_face.ratio_2_1 = data.get('ratio_2_1')
            existing_face.ratio_3_1 = data.get('ratio_3_1')
            existing_face.ratio_3_2 = data.get('ratio_3_2')
            existing_face.roll_angle = data.get('roll_angle')
            existing_face.ratios_detail = json.dumps(data.get('ratios_detail', {}))
            existing_face.landmarks = json.dumps(data.get('landmarks', []))
            existing_face.meta_data = json.dumps(data.get('metadata', {}))

            # 기존 랜드마크 삭제
            session.query(Landmark).filter_by(face_data_id=existing_face.id).delete()

            # 새 랜드마크 추가
            landmarks_added = self._process_landmarks(session, existing_face.id, data.get('landmarks', []))

            session.commit()

            print(f"   🔄 얼굴 데이터 업데이트: {existing_face.name}")
            print(f"      - 랜드마크: {landmarks_added}개")

            return True

        except Exception as e:
            session.rollback()
            print(f"❌ 얼굴 데이터 업데이트 실패: {e}")
            return False

    def _process_landmarks(self, session, face_data_id, landmarks_data):
        """랜드마크 데이터 처리"""
        if not landmarks_data:
            return 0

        landmarks_added = 0

        try:
            for point in landmarks_data:
                if isinstance(point, dict):
                    # mpidx 키 확인 (여러 가능한 키 지원)
                    mp_idx = point.get('mpidx') or point.get('mp_idx') or point.get('index') or point.get('id')
                    x = point.get('x')
                    y = point.get('y')
                    z = point.get('z')

                    if mp_idx is not None and x is not None and y is not None:
                        landmark = Landmark(
                            face_data_id=face_data_id,
                            mp_idx=int(mp_idx),
                            x=float(x),
                            y=float(y),
                            z=float(z) if z is not None else None
                        )
                        session.add(landmark)
                        landmarks_added += 1

        except Exception as e:
            print(f"⚠️ 랜드마크 처리 오류: {e}")

        return landmarks_added

    def get_processing_stats(self):
        """처리 통계 조회"""
        with db_manager.get_session() as session:
            face_count = session.query(FaceData).count()
            landmark_count = session.query(Landmark).count()

            return {
                'face_count': face_count,
                'landmark_count': landmark_count
            }

def main():
    """테스트용 메인 함수"""
    processor = DataProcessor()

    # 통계 출력
    stats = processor.get_processing_stats()
    print(f"📊 현재 DB 상태:")
    print(f"   - 얼굴 데이터: {stats['face_count']}개")
    print(f"   - 랜드마크: {stats['landmark_count']:,}개")

if __name__ == "__main__":
    main()