"""
데이터베이스 모델 정의
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
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
    meta_data = Column(Text)       # 추가 메타데이터 JSON

    # 관계
    tags = relationship("Tag", back_populates="face_data")
    custom_variables = relationship("CustomVariable", back_populates="face_data")

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
            'metadata': json.loads(self.meta_data) if self.meta_data else {},
            'tags': [tag.tag_name for tag in self.tags]
        }


class Tag(Base):
    """태그 테이블"""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    face_data_id = Column(Integer, ForeignKey('face_data.id'), nullable=False)
    tag_name = Column(String(100), nullable=False)

    # 관계
    face_data = relationship("FaceData", back_populates="tags")


class CustomVariable(Base):
    """사용자 정의 계산 변수"""
    __tablename__ = 'custom_variables'

    id = Column(Integer, primary_key=True, autoincrement=True)
    face_data_id = Column(Integer, ForeignKey('face_data.id'), nullable=False)
    variable_name = Column(String(100), nullable=False)
    variable_value = Column(Float)
    calculation_formula = Column(String(500))  # "ratio_2 / ratio_3" 같은 공식

    # 관계
    face_data = relationship("FaceData", back_populates="custom_variables")


class AnalysisConfig(Base):
    """저장된 분석 설정"""
    __tablename__ = 'analysis_configs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    config_json = Column(Text, nullable=False)  # 분석 설정 JSON
    created_date = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    use_count = Column(Integer, default=0)
    tags = Column(String(500))  # 태그들 (콤마 구분)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'config': json.loads(self.config_json) if self.config_json else {},
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'use_count': self.use_count,
            'tags': self.tags.split(',') if self.tags else []
        }


class AnalysisResult(Base):
    """분석 결과 캐시"""
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_hash = Column(String(64), nullable=False)  # 설정의 해시값
    result_data = Column(Text, nullable=False)        # 결과 JSON
    created_date = Column(DateTime, default=datetime.utcnow)
    file_count = Column(Integer)                      # 분석된 파일 수

    def to_dict(self):
        return {
            'id': self.id,
            'config_hash': self.config_hash,
            'result': json.loads(self.result_data) if self.result_data else {},
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'file_count': self.file_count
        }