#!/usr/bin/env python3
"""
데이터베이스 전용 서비스
"""
import os
import sys
from typing import List, Dict, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema_def import FaceData, FaceBasicMeasurements, Landmark, Tag, TagMeasurementDefinition, TagThreshold, FaceMeasurementValue
import pandas as pd
import json
import hashlib
from datetime import datetime
import math
from pathlib import Path
from sqlalchemy.orm import Session

class DatabaseCRUD:
    """데이터베이스 전용 서비스"""

    def __init__(self):
        self._tag_classification_cache = None
        print("🗄️ 데이터베이스 서비스 초기화 완료")

    # ==================== 데이터 조회 및 분석 ====================

    def query_data(self, filters=None):
        """데이터 쿼리"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            query = session.query(FaceData).join(FaceBasicMeasurements, isouter=True)

            if filters:
                # 태그 필터
                if 'tags' in filters and filters['tags']:
                    tag_conditions = []
                    for tag in filters['tags']:
                        query = query.join(Tag).filter(Tag.tag_name.like(f'%{tag}%'))

                # 날짜 필터
                if 'date_range' in filters and filters['date_range']:
                    start_date, end_date = filters['date_range']
                    query = query.filter(FaceData.upload_date.between(start_date, end_date))

                # 비율 범위 필터
                if 'ratio_x_range' in filters and filters['ratio_x_range']:
                    min_val, max_val = filters['ratio_x_range']
                    query = query.filter(FaceBasicMeasurements.ratio_2.between(min_val, max_val))

                if 'ratio_y_range' in filters and filters['ratio_y_range']:
                    min_val, max_val = filters['ratio_y_range']
                    query = query.filter(FaceBasicMeasurements.ratio_3.between(min_val, max_val))

            results = query.all()
            return [result.to_dict() for result in results]

    def get_dataframe(self, filters=None):
        """pandas DataFrame으로 데이터 반환"""
        data = self.query_data(filters)
        if not data:
            return pd.DataFrame()

        # 태그들을 문자열로 변환
        for item in data:
            item['tags_str'] = ', '.join(item.get('tags', []))
            item['tag_count'] = len(item.get('tags', []))

        return pd.DataFrame(data)

    def get_available_variables(self):
        """사용 가능한 변수 목록 반환"""
        base_vars = [
            'ratio_1', 'ratio_2', 'ratio_3', 'ratio_4', 'ratio_5',
            'ratio_2_1', 'ratio_3_1', 'ratio_3_2',
            'roll_angle', 'tag_count'
        ]

        # 커스텀 변수들 추가 (현재는 스키마에 없음)
        # with db_manager.get_session() as session:
        #     custom_vars = session.query(CustomVariable.variable_name).distinct().all()
        #     custom_var_names = [var[0] for var in custom_vars]

        return base_vars  # + custom_var_names



    # ==================== 얼굴 데이터 조회 ====================

    def get_all_faces(self) -> List[Dict]:
        """모든 얼굴 데이터 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            faces = session.query(FaceData).all()
            return [face.to_dict() for face in faces]

    def get_face_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 얼굴 데이터 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            face = session.query(FaceData).filter_by(name=name).first()
            return face.to_dict() if face else None

    def get_face_by_id(self, face_id: int) -> Optional[Dict]:
        """ID로 얼굴 데이터 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            face = session.query(FaceData).filter_by(id=face_id).first()
            return face.to_dict() if face else None

    # ==================== 랜드마크 데이터 조회 ====================

    def get_landmarks_by_face_id(self, face_id: int) -> List[Dict]:
        """얼굴 ID로 랜드마크 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            landmarks = session.query(Landmark).filter_by(face_data_id=face_id).all()
            return [landmark.to_dict() for landmark in landmarks]

    def get_landmark_by_mpidx(self, face_id: int, mp_idx: int) -> Optional[Dict]:
        """특정 MediaPipe 인덱스 랜드마크 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            landmark = session.query(Landmark).filter_by(
                face_data_id=face_id,
                mp_idx=mp_idx
            ).first()
            return landmark.to_dict() if landmark else None

    def get_landmarks_by_mpidx_list(self, face_id: int, mp_idx_list: List[int]) -> List[Dict]:
        """여러 MediaPipe 인덱스 랜드마크 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            landmarks = session.query(Landmark).filter(
                Landmark.face_data_id == face_id,
                Landmark.mp_idx.in_(mp_idx_list)
            ).all()
            return [landmark.to_dict() for landmark in landmarks]

    # ==================== 측정 정의 조회 ====================

    def get_all_measurement_definitions(self) -> List[Dict]:
        """모든 측정 정의 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            definitions = session.query(TagMeasurementDefinition).all()
            return [definition.to_dict() for definition in definitions]

    def get_measurement_definition_by_tag(self, tag_name: str) -> Optional[Dict]:
        """태그 이름으로 측정 정의 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            definition = session.query(TagMeasurementDefinition).filter_by(tag_name=tag_name).first()
            return definition.to_dict() if definition else None

    def get_measurement_definitions_by_type(self, measurement_type: str) -> List[Dict]:
        """측정 타입으로 정의들 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            definitions = session.query(TagMeasurementDefinition).filter_by(
                measurement_type=measurement_type
            ).all()
            return [definition.to_dict() for definition in definitions]

    # ==================== 태그 관리 ====================

    def get_tags_by_face_id(self, face_id: int) -> List[str]:
        """얼굴 ID로 태그들 조회"""
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            tags = session.query(Tag).filter_by(face_data_id=face_id).all()
            return [tag.tag_name for tag in tags]


    # ==================== 태그 분류 및 처리 ====================

    def get_tag_classification(self):
        """태그 분류 정보 로드 (캐싱)"""
        if self._tag_classification_cache is None:
            try:
                classification_path = Path("source_data/tag_classification.json")
                with open(classification_path, 'r', encoding='utf-8') as f:
                    self._tag_classification_cache = json.load(f)
            except Exception as e:
                print(f"태그 분류 파일 로드 실패: {e}")
                # 기본값 반환
                self._tag_classification_cache = {
                    "tag_levels": {
                        "0": {"tags": []},
                        "1": {"tags": []},
                        "2": {"tags": []}
                    }
                }
        return self._tag_classification_cache

    def determine_tag_level(self, tag_name):
        """태그명으로 레벨 판단"""
        classification = self.get_tag_classification()

        # 0차, 1차 태그 목록에서 검색
        for level in ["0", "1"]:
            if tag_name in classification["tag_levels"][level]["tags"]:
                return int(level)

        # 2차 태그 패턴 검사 (측정값 태그: "부위-속성-값" 형태)
        if '-' in tag_name and len(tag_name.split('-')) >= 3:
            return 2

        # 기본값: 1차 태그로 분류
        return 1

    def auto_generate_secondary_tags(self, session: Session, face_data_id: int, landmarks):
        """임계값 기반 2차 태그 자동 생성"""
        if not landmarks:
            return

        # 모든 태그 카테고리와 측정 정의 가져오기
        tag_definitions = session.query(TagMeasurementDefinition).all()

        for definition in tag_definitions:
            try:
                # 측정값 계산
                calculated_value = self.calculate_measurement_value(landmarks, definition)

                # 1. 측정값 저장 (None이어도 저장)
                measurement_value = FaceMeasurementValue(
                    face_data_id=face_data_id,
                    tag_name=definition.tag_name,
                    측정값=calculated_value
                )
                session.add(measurement_value)

                # 2. 값이 있을 때만 임계값 분류 및 태그 저장
                if calculated_value is not None:
                    tag_value = self.classify_by_threshold(session, definition.tag_name, calculated_value)

                    if tag_value:
                        # 3. 2차 태그 저장
                        secondary_tag = Tag(
                            face_data_id=face_data_id,
                            tag_name=definition.tag_name,  # "eye-길이"
                            tag_level=2,
                            tag_value=tag_value  # "긴", "보통", "짧은"
                        )
                        session.add(secondary_tag)

            except Exception as e:
                print(f"Error generating secondary tag for {definition.tag_name}: {e}")
                continue

    def calculate_measurement_value(self, landmarks, definition):
        """측정 정의에 따른 실제 측정값 계산"""
        if not landmarks or not definition:
            return None

        # landmarks를 dict로 변환 (mpidx를 key로)
        landmarks_dict = {}
        for lm in landmarks:
            if isinstance(lm, dict) and 'mpidx' in lm:
                landmarks_dict[lm['mpidx']] = lm

        try:
            if definition.measurement_type == "길이":
                # 길이 측정 (분자만 사용)
                if definition.분자_점1 is not None and definition.분자_점2 is not None:
                    if definition.분자_점1 not in landmarks_dict or definition.분자_점2 not in landmarks_dict:
                        return None

                    p1 = landmarks_dict[definition.분자_점1]
                    p2 = landmarks_dict[definition.분자_점2]

                    # 거리 계산 방식에 따라
                    if definition.거리계산방식 == "직선거리":
                        distance = math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)
                    elif definition.거리계산방식 == "x좌표거리":
                        distance = abs(p1['x'] - p2['x'])
                    elif definition.거리계산방식 == "y좌표거리":
                        distance = abs(p1['y'] - p2['y'])
                    else:
                        distance = math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)

                    return distance

            elif definition.measurement_type == "비율":
                # 비율 측정 (분자/분모)
                if (definition.분자_점1 is not None and definition.분자_점2 is not None and
                    definition.분모_점1 is not None and definition.분모_점2 is not None):

                    if (definition.분자_점1 not in landmarks_dict or definition.분자_점2 not in landmarks_dict or
                        definition.분모_점1 not in landmarks_dict or definition.분모_점2 not in landmarks_dict):
                        return None

                    # 분자 거리
                    num_p1 = landmarks_dict[definition.분자_점1]
                    num_p2 = landmarks_dict[definition.분자_점2]

                    # 분모 거리
                    den_p1 = landmarks_dict[definition.분모_점1]
                    den_p2 = landmarks_dict[definition.분모_점2]

                    # 거리 계산 방식에 따라
                    if definition.거리계산방식 == "직선거리":
                        numerator = math.sqrt((num_p1['x'] - num_p2['x'])**2 + (num_p1['y'] - num_p2['y'])**2)
                        denominator = math.sqrt((den_p1['x'] - den_p2['x'])**2 + (den_p1['y'] - den_p2['y'])**2)
                    elif definition.거리계산방식 == "x좌표거리":
                        numerator = abs(num_p1['x'] - num_p2['x'])
                        denominator = abs(den_p1['x'] - den_p2['x'])
                    elif definition.거리계산방식 == "y좌표거리":
                        numerator = abs(num_p1['y'] - num_p2['y'])
                        denominator = abs(den_p1['y'] - den_p2['y'])
                    else:
                        numerator = math.sqrt((num_p1['x'] - num_p2['x'])**2 + (num_p1['y'] - num_p2['y'])**2)
                        denominator = math.sqrt((den_p1['x'] - den_p2['x'])**2 + (den_p1['y'] - den_p2['y'])**2)

                    if denominator != 0:
                        return numerator / denominator

            elif definition.measurement_type == "곡률":
                # 곡률 측정 (향후 구현)
                return None

        except (IndexError, KeyError, TypeError) as e:
            print(f"Error calculating measurement for {definition.tag_name}: {e}")
            return None

        return None

    def classify_by_threshold(self, session: Session, tag_name: str, value: float):
        """임계값에 따른 태그 값 분류"""
        thresholds = session.query(TagThreshold).filter_by(tag_name=tag_name).all()

        for threshold in thresholds:
            if (threshold.min_threshold is None or value >= threshold.min_threshold) and \
               (threshold.max_threshold is None or value < threshold.max_threshold):
                return threshold.value_name

        return None

    def process_tags_for_face(self, session, face_data_id: int, tags_data, landmarks=None):
        """얼굴 데이터에 태그들을 처리하여 추가 (공통 로직)"""
        tags = tags_data or []
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]

        for tag in tags:
            if tag.strip():
                tag_level = self.determine_tag_level(tag)

                if tag_level == 2 and '-' in tag and len(tag.split('-')) >= 3:
                    # "eye-길이-긴" 형태 -> 2차 태그 분리
                    parts = tag.split('-')
                    tag_category = f"{parts[0]}-{parts[1]}"  # "eye-길이"
                    tag_value = parts[2]  # "긴"
                    tag_obj = Tag(
                        face_data_id=face_data_id,
                        tag_name=tag_category,
                        tag_level=tag_level,
                        tag_value=tag_value
                    )
                else:
                    # 0차, 1차 태그 또는 패턴이 맞지 않는 태그
                    tag_obj = Tag(
                        face_data_id=face_data_id,
                        tag_name=tag.strip(),
                        tag_level=tag_level,
                        tag_value=None
                    )
                session.add(tag_obj)

        # 2차 태그 자동 생성 (임계값 기반)
        if landmarks:
            self.auto_generate_secondary_tags(session, face_data_id, landmarks)

        # Landmark 데이터를 별도 테이블에 저장
        if landmarks:
            self.save_landmarks_to_table(session, face_data_id, landmarks)

    def save_landmarks_to_table(self, session, face_data_id: int, landmarks):
        """landmarks 데이터를 별도 Landmark 테이블에 저장"""
        if not landmarks:
            return

        # 기존 landmarks 삭제 (중복 방지)
        session.query(Landmark).filter_by(face_data_id=face_data_id).delete()

        # landmarks가 JSON 문자열인 경우 파싱
        if isinstance(landmarks, str):
            import json
            try:
                landmarks = json.loads(landmarks)
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON in landmarks for face_data_id {face_data_id}")
                return

        # 각 landmark 포인트를 테이블에 저장 (소수점 3자리까지만)
        for landmark in landmarks:
            if isinstance(landmark, dict) and 'mpidx' in landmark:
                landmark_obj = Landmark(
                    face_data_id=face_data_id,
                    mp_idx=landmark.get('mpidx'),
                    x=round(landmark.get('x', 0.0), 3),
                    y=round(landmark.get('y', 0.0), 3),
                    z=round(landmark.get('z', 0.0), 3) if landmark.get('z') is not None else None
                )
                session.add(landmark_obj)

    def remove_all_tags_for_face(self, session, face_data_id: int):
        """특정 얼굴의 모든 태그 삭제"""
        session.query(Tag).filter_by(face_data_id=face_data_id).delete()

    def remove_all_landmarks_for_face(self, session, face_data_id: int):
        """특정 얼굴의 모든 landmarks 삭제"""
        session.query(Landmark).filter_by(face_data_id=face_data_id).delete()

    # ==================== 통계 ====================

    def get_database_stats(self) -> Dict:
        """데이터베이스 통계"""
        from database.connect_db import db_manager
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
        from database.connect_db import db_manager
        with db_manager.get_session() as session:
            # JOIN 쿼리
            faces = session.query(FaceData).join(Tag).filter(
                Tag.tag_name == tag_name
            ).all()

            return [face.to_dict() for face in faces]

    # ==================== 데이터 생성 ====================

    def create_face_data_from_json(self, session, json_data, name=None):
        """JSON 데이터로부터 FaceData 객체 생성 및 태그 추가 (공통 로직)"""
        from utils.ratio_parser import RatioParser
        import json
        from datetime import datetime

        parser = RatioParser()
        ratio_components = parser.parse_ratio_to_components(json_data.get('faceRatio', ''))

        # FaceData 객체 생성 (기본 정보만)
        face_data = FaceData(
            name=name or json_data.get('name', 'unknown'),
            json_file_path=json_data.get('_filename', ''),
            image_file_path=None  # 추후 연동
        )

        session.add(face_data)
        session.flush()  # ID 생성을 위해

        # FaceBasicMeasurements 객체 생성 (수치 데이터)
        measurements = FaceBasicMeasurements(
            face_data_id=face_data.id,
            roll_angle=json_data.get('rollAngle', 0),
            face_basic_ratio=json_data.get('faceRatio', ''),
            ratio_1=ratio_components.get('ratio_1'),
            ratio_2=ratio_components.get('ratio_2'),
            ratio_3=ratio_components.get('ratio_3'),
            ratio_4=ratio_components.get('ratio_4'),
            ratio_5=ratio_components.get('ratio_5'),
            ratio_2_1=ratio_components.get('ratio_2_1'),
            ratio_3_1=ratio_components.get('ratio_3_1'),
            ratio_3_2=ratio_components.get('ratio_3_2')
        )

        session.add(measurements)

        # 태그 처리 (통합된 메서드 사용)
        self.process_tags_for_face(
            session,
            face_data.id,
            json_data.get('tags', []),
            json_data.get('landmarks', [])
        )

        return face_data

    def update_face_tags(self, session, face_id: int, tags_data, landmarks=None):
        """기존 얼굴의 태그 업데이트"""
        
        # 기존 태그 삭제 후 새 태그 추가
        self.remove_all_tags_for_face(session, face_id)
        self.process_tags_for_face(session, face_id, tags_data, landmarks)

    def delete_face_data(self, session, face_data):
        """얼굴 데이터 및 관련 태그 삭제"""
        
        # 관련 태그 먼저 삭제
        self.remove_all_tags_for_face(session, face_data.id)
        # 레코드 삭제
        session.delete(face_data)

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

# 전역 CRUD 서비스 인스턴스
crud_service = DatabaseCRUD()

if __name__ == "__main__":
    main()