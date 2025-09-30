"""
데이터베이스 모델 정의
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class FaceData(Base):
    """메인 얼굴 데이터 테이블"""
    __tablename__ = 'face_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    upload_date = Column(DateTime, default=datetime.utcnow)

    # 원본 비율 데이터
    face_ratio_raw = Column(String(100))  # "1:1.2:0.8" 형태

    # 파싱된 비율 컴포넌트들
    ratio_1 = Column(Float)
    ratio_2 = Column(Float)
    ratio_3 = Column(Float)
    ratio_4 = Column(Float)
    ratio_5 = Column(Float)

    # 계산된 비율들
    ratio_2_1 = Column(Float)  # ratio_2 / ratio_1
    ratio_3_1 = Column(Float)  # ratio_3 / ratio_1
    ratio_3_2 = Column(Float)  # ratio_3 / ratio_2

    # 기타 측정값들
    roll_angle = Column(Float)

    # JSON 데이터들
    ratios_detail = Column(Text)  # 상세 비율 정보 JSON
    landmarks = Column(Text)       # 랜드마크 좌표 JSON (492개 점)
    meta_data = Column(Text)       # 추가 메타데이터 JSON

    # 관계
    tags = relationship("Tag", back_populates="face_data")
    landmarks_points = relationship("Landmark", back_populates="face_data")

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'file_path': self.file_path,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'face_ratio_raw': self.face_ratio_raw,
            'ratio_1': self.ratio_1,
            'ratio_2': self.ratio_2,
            'ratio_3': self.ratio_3,
            'ratio_4': self.ratio_4,
            'ratio_5': self.ratio_5,
            'ratio_2_1': self.ratio_2_1,
            'ratio_3_1': self.ratio_3_1,
            'ratio_3_2': self.ratio_3_2,
            'roll_angle': self.roll_angle,
            'ratios_detail': json.loads(self.ratios_detail) if self.ratios_detail else {},
            'landmarks': json.loads(self.landmarks) if self.landmarks else [],
            'metadata': json.loads(self.meta_data) if self.meta_data else {},
            'tags': [tag.tag_name for tag in self.tags]
        }


class Tag(Base):
    """태그 테이블"""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    face_data_id = Column(Integer, ForeignKey('face_data.id'), nullable=False)
    tag_name = Column(String(100), nullable=False)
    tag_level = Column(Integer, nullable=False)  # 0: 추상, 1: 구체적, 2: 측정값 기반

    # 관계
    face_data = relationship("FaceData", back_populates="tags")

    def to_dict(self):
        return {
            'id': self.id,
            'face_data_id': self.face_data_id,
            'tag_name': self.tag_name,
            'tag_level': self.tag_level
        }


class Landmark(Base):
    """개별 랜드마크 좌표 테이블"""
    __tablename__ = 'landmarks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    face_data_id = Column(Integer, ForeignKey('face_data.id'), nullable=False)
    mp_idx = Column(Integer, nullable=False)  # MediaPipe 인덱스 (0~491, 500)
    x = Column(Float, nullable=False)         # X 좌표
    y = Column(Float, nullable=False)         # Y 좌표
    z = Column(Float)                         # Z 좌표 (있는 경우)

    # 관계
    face_data = relationship("FaceData", back_populates="landmarks_points")

    def to_dict(self):
        return {
            'id': self.id,
            'face_data_id': self.face_data_id,
            'mp_idx': self.mp_idx,
            'x': self.x,
            'y': self.y,
            'z': self.z
        }


class TagMeasurementDefinition(Base):
    """태그 측정 정의 테이블"""
    __tablename__ = 'tag_measurement_definitions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(100), unique=True, nullable=False)
    measurement_type = Column(String(20), nullable=False)  # "길이", "비율", "곡률"
    description = Column(Text)

    # 길이 측정용
    point1_mpidx = Column(Integer)
    point2_mpidx = Column(Integer)

    # 비율 측정용 - 분모
    denominator_point1 = Column(Integer)
    denominator_point2 = Column(Integer)

    # 비율 측정용 - 분자
    numerator_point1 = Column(Integer)
    numerator_point2 = Column(Integer)

    # 곡률 측정용
    curvature_points = Column(JSON)

    def to_dict(self):
        return {
            'id': self.id,
            'tag_name': self.tag_name,
            'measurement_type': self.measurement_type,
            'description': self.description,
            'point1_mpidx': self.point1_mpidx,
            'point2_mpidx': self.point2_mpidx,
            'denominator_point1': self.denominator_point1,
            'denominator_point2': self.denominator_point2,
            'numerator_point1': self.numerator_point1,
            'numerator_point2': self.numerator_point2,
            'curvature_points': self.curvature_points
        }