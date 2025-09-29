#!/usr/bin/env python3
"""
JSON 랜드마크 데이터를 개별 landmarks 테이블로 변환하는 스크립트
"""
import os
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager
from database.models import FaceData, Landmark

def convert_json_landmarks_to_table():
    """JSON 랜드마크를 개별 테이블로 변환"""
    print("🔄 랜드마크 데이터 변환 시작...")
    print("=" * 60)

    # 1. 새 landmarks 테이블 생성
    print("📋 새 테이블 생성 중...")
    try:
        from database.models import Base
        Base.metadata.create_all(bind=db_manager.engine)
        print("✅ landmarks 테이블 생성 완료")
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        return False

    # 2. 기존 face_data에서 landmarks JSON 추출
    converted_count = 0
    error_count = 0

    with db_manager.get_session() as session:
        # 모든 face_data 조회
        face_records = session.query(FaceData).all()
        print(f"📊 변환 대상: {len(face_records)}개 얼굴 데이터")

        for face_record in face_records:
            try:
                print(f"\n🔍 처리 중: {face_record.name}")

                # JSON 랜드마크 데이터 파싱
                if not face_record.landmarks:
                    print(f"⚠️ {face_record.name}: 랜드마크 데이터 없음")
                    continue

                landmarks_data = json.loads(face_record.landmarks)
                if not landmarks_data:
                    print(f"⚠️ {face_record.name}: 빈 랜드마크 데이터")
                    continue

                # 기존 landmarks 레코드 삭제 (재실행 시)
                session.query(Landmark).filter_by(face_data_id=face_record.id).delete()

                # 개별 랜드마크 포인트 저장
                landmark_count = 0
                for point in landmarks_data:
                    try:
                        # 다양한 JSON 구조 지원
                        if isinstance(point, dict):
                            mp_idx = point.get('mpidx') or point.get('mp_idx') or point.get('index') or point.get('id')
                            x = point.get('x')
                            y = point.get('y')
                            z = point.get('z')  # 있을 수도 있고 없을 수도
                        else:
                            continue

                        if mp_idx is None or x is None or y is None:
                            continue

                        # Landmark 레코드 생성
                        landmark = Landmark(
                            face_data_id=face_record.id,
                            mp_idx=int(mp_idx),
                            x=float(x),
                            y=float(y),
                            z=float(z) if z is not None else None
                        )
                        session.add(landmark)
                        landmark_count += 1

                    except (ValueError, TypeError) as e:
                        print(f"   ⚠️ 포인트 변환 오류: {e}")
                        continue

                print(f"   ✅ {landmark_count}개 랜드마크 변환됨")
                converted_count += 1

            except Exception as e:
                print(f"❌ {face_record.name} 변환 실패: {e}")
                error_count += 1
                continue

        # 커밋
        session.commit()

    print(f"\n🎉 변환 완료!")
    print(f"   ✅ 성공: {converted_count}개")
    print(f"   ❌ 실패: {error_count}개")

    # 3. 결과 확인
    print(f"\n📊 변환 결과 확인...")
    with db_manager.get_session() as session:
        total_landmarks = session.query(Landmark).count()
        print(f"   총 랜드마크 포인트: {total_landmarks:,}개")

        # 샘플 확인
        sample = session.query(Landmark).limit(5).all()
        print(f"   샘플 데이터:")
        for landmark in sample:
            print(f"     - ID:{landmark.face_data_id}, mp_idx:{landmark.mp_idx}, x:{landmark.x:.2f}, y:{landmark.y:.2f}")

    return True

def test_performance():
    """성능 테스트"""
    print(f"\n⚡ 성능 테스트...")

    import time
    from sqlalchemy import text

    with db_manager.get_session() as session:
        # 기존 방식 (JSON 파싱)
        print("🐌 기존 방식 (JSON 파싱):")
        start_time = time.time()
        face_records = session.query(FaceData).limit(5).all()
        for face_record in face_records:
            if face_record.landmarks:
                landmarks_data = json.loads(face_record.landmarks)
                # 점 33번 찾기
                for point in landmarks_data:
                    if isinstance(point, dict) and point.get('mpidx') == 33:
                        break
        old_time = time.time() - start_time

        # 새 방식 (직접 쿼리)
        print("🚀 새 방식 (직접 쿼리):")
        start_time = time.time()
        for face_record in face_records:
            result = session.query(Landmark).filter_by(
                face_data_id=face_record.id,
                mp_idx=33
            ).first()
        new_time = time.time() - start_time

        print(f"   기존 방식: {old_time:.4f}초")
        print(f"   새 방식: {new_time:.4f}초")
        if old_time > 0:
            speedup = old_time / new_time
            print(f"   속도 향상: {speedup:.1f}배 빨라짐!")

def main():
    """메인 함수"""
    print("🎯 랜드마크 데이터 구조 최적화")
    print("   JSON 통문자열 → 개별 테이블 변환")
    print("=" * 60)

    # 변환 실행
    if convert_json_landmarks_to_table():
        # 성능 테스트
        test_performance()

        print(f"\n✨ 모든 작업 완료!")
        print(f"💡 이제 다음과 같이 빠른 쿼리가 가능합니다:")
        print(f"   - 특정 점 찾기: session.query(Landmark).filter_by(mp_idx=33)")
        print(f"   - 얼굴별 점들: session.query(Landmark).filter_by(face_data_id=1)")
        print(f"   - 거리 계산: 두 점의 좌표 직접 조회")
    else:
        print(f"\n❌ 변환 실패")

if __name__ == "__main__":
    main()