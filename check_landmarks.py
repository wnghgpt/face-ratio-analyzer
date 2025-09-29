#!/usr/bin/env python3
"""
랜드마크 변환 결과 확인 스크립트
"""
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager
from database.models import FaceData, Landmark
from sqlalchemy import text

def check_conversion_status():
    """변환 상태 확인"""
    print("🔍 랜드마크 변환 상태 확인")
    print("=" * 50)

    with db_manager.get_session() as session:
        # 1. 기본 테이블 확인
        face_count = session.query(FaceData).count()
        landmark_count = session.query(Landmark).count()

        print(f"📊 데이터 현황:")
        print(f"   얼굴 데이터: {face_count}개")
        print(f"   랜드마크 포인트: {landmark_count:,}개")

        if landmark_count == 0:
            print("\n❌ 랜드마크 데이터가 없습니다!")

            # 원본 JSON 데이터 확인
            print("\n🔍 원본 데이터 확인:")
            sample_faces = session.query(FaceData).limit(3).all()
            for face in sample_faces:
                if face.landmarks:
                    import json
                    try:
                        landmarks_data = json.loads(face.landmarks)
                        print(f"   {face.name}: {len(landmarks_data)}개 포인트 (JSON)")
                        if len(landmarks_data) > 0:
                            first_point = landmarks_data[0]
                            print(f"     첫 번째 포인트: {first_point}")
                    except Exception as e:
                        print(f"   {face.name}: JSON 파싱 오류 - {e}")
                else:
                    print(f"   {face.name}: 랜드마크 데이터 없음")
        else:
            # 샘플 데이터 확인
            print(f"\n✅ 변환 성공! 샘플 데이터:")
            samples = session.query(Landmark).limit(10).all()
            for landmark in samples:
                print(f"   ID:{landmark.face_data_id}, mp_idx:{landmark.mp_idx}, x:{landmark.x:.2f}, y:{landmark.y:.2f}")

            # 얼굴별 랜드마크 수 확인
            print(f"\n📈 얼굴별 랜드마크 수:")
            result = session.execute(text("""
                SELECT fd.name, COUNT(l.id) as landmark_count
                FROM face_data fd
                LEFT JOIN landmarks l ON fd.id = l.face_data_id
                GROUP BY fd.id, fd.name
                ORDER BY landmark_count DESC
                LIMIT 10
            """)).fetchall()

            for row in result:
                print(f"   {row[0]}: {row[1]}개")

def main():
    check_conversion_status()

if __name__ == "__main__":
    main()