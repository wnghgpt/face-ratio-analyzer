#!/usr/bin/env python3
"""
데이터베이스 전용 서비스
"""
import os
import sys
from typing import List, Dict, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connect_db import db_manager
from database.schema_def import FaceData, Landmark, Tag, TagMeasurementDefinition

class DatabaseCRUD:
    """데이터베이스 전용 서비스"""

    def __init__(self):
        print("🗄️ 데이터베이스 서비스 초기화 완료")

    # ==================== 얼굴 데이터 조회 ====================

    def get_all_faces(self) -> List[Dict]:
        """모든 얼굴 데이터 조회"""
        with db_manager.get_session() as session:
            faces = session.query(FaceData).all()
            return [face.to_dict() for face in faces]

    def get_face_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 얼굴 데이터 조회"""
        with db_manager.get_session() as session:
            face = session.query(FaceData).filter_by(name=name).first()
            return face.to_dict() if face else None

    def get_face_by_id(self, face_id: int) -> Optional[Dict]:
        """ID로 얼굴 데이터 조회"""
        with db_manager.get_session() as session:
            face = session.query(FaceData).filter_by(id=face_id).first()
            return face.to_dict() if face else None

    # ==================== 랜드마크 데이터 조회 ====================

    def get_landmarks_by_face_id(self, face_id: int) -> List[Dict]:
        """얼굴 ID로 랜드마크 조회"""
        with db_manager.get_session() as session:
            landmarks = session.query(Landmark).filter_by(face_data_id=face_id).all()
            return [landmark.to_dict() for landmark in landmarks]

    def get_landmark_by_mpidx(self, face_id: int, mp_idx: int) -> Optional[Dict]:
        """특정 MediaPipe 인덱스 랜드마크 조회"""
        with db_manager.get_session() as session:
            landmark = session.query(Landmark).filter_by(
                face_data_id=face_id,
                mp_idx=mp_idx
            ).first()
            return landmark.to_dict() if landmark else None

    def get_landmarks_by_mpidx_list(self, face_id: int, mp_idx_list: List[int]) -> List[Dict]:
        """여러 MediaPipe 인덱스 랜드마크 조회"""
        with db_manager.get_session() as session:
            landmarks = session.query(Landmark).filter(
                Landmark.face_data_id == face_id,
                Landmark.mp_idx.in_(mp_idx_list)
            ).all()
            return [landmark.to_dict() for landmark in landmarks]

    # ==================== 측정 정의 조회 ====================

    def get_all_measurement_definitions(self) -> List[Dict]:
        """모든 측정 정의 조회"""
        with db_manager.get_session() as session:
            definitions = session.query(TagMeasurementDefinition).all()
            return [definition.to_dict() for definition in definitions]

    def get_measurement_definition_by_tag(self, tag_name: str) -> Optional[Dict]:
        """태그 이름으로 측정 정의 조회"""
        with db_manager.get_session() as session:
            definition = session.query(TagMeasurementDefinition).filter_by(tag_name=tag_name).first()
            return definition.to_dict() if definition else None

    def get_measurement_definitions_by_type(self, measurement_type: str) -> List[Dict]:
        """측정 타입으로 정의들 조회"""
        with db_manager.get_session() as session:
            definitions = session.query(TagMeasurementDefinition).filter_by(
                measurement_type=measurement_type
            ).all()
            return [definition.to_dict() for definition in definitions]

    # ==================== 태그 관리 ====================

    def get_tags_by_face_id(self, face_id: int) -> List[str]:
        """얼굴 ID로 태그들 조회"""
        with db_manager.get_session() as session:
            tags = session.query(Tag).filter_by(face_data_id=face_id).all()
            return [tag.tag_name for tag in tags]

    def add_tag_to_face(self, face_id: int, tag_name: str) -> bool:
        """얼굴에 태그 추가"""
        try:
            with db_manager.get_session() as session:
                # 중복 확인
                existing = session.query(Tag).filter_by(
                    face_data_id=face_id,
                    tag_name=tag_name
                ).first()

                if existing:
                    return True  # 이미 존재함

                # 새 태그 추가
                new_tag = Tag(face_data_id=face_id, tag_name=tag_name)
                session.add(new_tag)
                session.commit()

                return True

        except Exception as e:
            print(f"❌ 태그 추가 실패: {e}")
            return False

    def remove_tag_from_face(self, face_id: int, tag_name: str) -> bool:
        """얼굴에서 태그 제거"""
        try:
            with db_manager.get_session() as session:
                tag = session.query(Tag).filter_by(
                    face_data_id=face_id,
                    tag_name=tag_name
                ).first()

                if tag:
                    session.delete(tag)
                    session.commit()

                return True

        except Exception as e:
            print(f"❌ 태그 제거 실패: {e}")
            return False

    # ==================== 통계 ====================

    def get_database_stats(self) -> Dict:
        """데이터베이스 통계"""
        with db_manager.get_session() as session:
            face_count = session.query(FaceData).count()
            landmark_count = session.query(Landmark).count()
            tag_count = session.query(Tag).count()
            definition_count = session.query(TagMeasurementDefinition).count()

            return {
                'face_count': face_count,
                'landmark_count': landmark_count,
                'tag_count': tag_count,
                'measurement_definition_count': definition_count
            }

    def get_faces_by_tag(self, tag_name: str) -> List[Dict]:
        """태그로 얼굴들 조회"""
        with db_manager.get_session() as session:
            # JOIN 쿼리
            faces = session.query(FaceData).join(Tag).filter(
                Tag.tag_name == tag_name
            ).all()

            return [face.to_dict() for face in faces]

    # ==================== 측정 계산 ====================

    def calculate_distance(self, face_id: int, point1_idx: int, point2_idx: int) -> Optional[float]:
        """두 점 간 직선 거리 계산"""
        landmarks = self.get_landmarks_by_mpidx_list(face_id, [point1_idx, point2_idx])

        if len(landmarks) != 2:
            return None

        point1 = landmarks[0] if landmarks[0]['mp_idx'] == point1_idx else landmarks[1]
        point2 = landmarks[1] if landmarks[1]['mp_idx'] == point1_idx else landmarks[0]

        # 유클리드 거리
        distance = ((point2['x'] - point1['x'])**2 + (point2['y'] - point1['y'])**2)**0.5
        return distance

    def calculate_measurement(self, face_id: int, tag_name: str) -> Optional[float]:
        """측정 정의에 따른 실제 측정값 계산"""
        definition = self.get_measurement_definition_by_tag(tag_name)

        if not definition:
            return None

        if definition['measurement_type'] == '길이':
            if definition['point1_mpidx'] and definition['point2_mpidx']:
                return self.calculate_distance(
                    face_id,
                    definition['point1_mpidx'],
                    definition['point2_mpidx']
                )

        elif definition['measurement_type'] == '비율':
            if (definition['denominator_point1'] and definition['denominator_point2'] and
                definition['numerator_point1'] and definition['numerator_point2']):

                denominator = self.calculate_distance(
                    face_id,
                    definition['denominator_point1'],
                    definition['denominator_point2']
                )

                numerator = self.calculate_distance(
                    face_id,
                    definition['numerator_point1'],
                    definition['numerator_point2']
                )

                if denominator and numerator and denominator != 0:
                    return numerator / denominator

        # 곡률 계산은 더 복잡하므로 일단 None 반환
        return None

def main():
    """테스트용 메인 함수"""
    service = DatabaseCRUD()

    # 통계 출력
    stats = service.get_database_stats()
    print(f"📊 데이터베이스 통계:")
    for key, value in stats.items():
        print(f"   - {key}: {value:,}")

    # 샘플 얼굴 조회
    faces = service.get_all_faces()
    if faces:
        print(f"\n👤 샘플 얼굴: {faces[0]['name']}")

if __name__ == "__main__":
    main()