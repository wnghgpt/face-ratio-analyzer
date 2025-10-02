"""
데이터베이스 모델 정의
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class PoolProfile(Base):
    """풀 프로필 테이블 - 기본 정보만"""
    __tablename__ = 'pool_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    json_file_path = Column(String(500))  # 원본 JSON 파일 경로
    image_file_path = Column(String(500))  # 원본 이미지 파일 경로
    upload_date = Column(DateTime, default=datetime.utcnow)

    # 관계
    tags = relationship("PoolTag", back_populates="profile", cascade="all, delete-orphan")
    landmarks_points = relationship("PoolLandmark", back_populates="profile", cascade="all, delete-orphan")
    basic_ratio = relationship("PoolBasicRatio", back_populates="profile", cascade="all, delete-orphan", uselist=False)
    measurement_values = relationship("Pool2ndTagValue", back_populates="profile", cascade="all, delete-orphan")

    def to_dict(self):
        """딕셔너리로 변환"""
        result = {
            'id': self.id,
            'name': self.name,
            'json_file_path': self.json_file_path,
            'image_file_path': self.image_file_path,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'tags': [tag.tag_name for tag in self.tags]
        }

        # basic_ratio가 있으면 포함
        if self.basic_ratio:
            result['basic_ratio'] = self.basic_ratio.to_dict()

        # landmarks가 있으면 포함
        if self.landmarks_points:
            result['landmarks'] = [lm.to_dict() for lm in self.landmarks_points]
        else:
            result['landmarks'] = None

        return result


class PoolBasicRatio(Base):
    """풀 기본 비율 테이블 - 정규화"""
    __tablename__ = 'pool_basic_ratio'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('pool_profiles.id'), nullable=False, unique=True)

    # 기본 각도
    roll_angle = Column(Float)

    # 원본 비율 데이터
    face_basic_ratio = Column(String(100))  # "1:1.2:0.8" 형태

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

    # 관계
    profile = relationship("PoolProfile", back_populates="basic_ratio")

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'roll_angle': self.roll_angle,
            'face_basic_ratio': self.face_basic_ratio,
            'ratio_1': self.ratio_1,
            'ratio_2': self.ratio_2,
            'ratio_3': self.ratio_3,
            'ratio_4': self.ratio_4,
            'ratio_5': self.ratio_5,
            'ratio_2_1': self.ratio_2_1,
            'ratio_3_1': self.ratio_3_1,
            'ratio_3_2': self.ratio_3_2
        }


class PoolTag(Base):
    """풀 태그 테이블"""
    __tablename__ = 'pool_tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('pool_profiles.id'), nullable=False)
    tag_name = Column(String(100), nullable=False)  # 0,1차: "얼굴형", 2차: "eye-길이"
    tag_level = Column(Integer, nullable=False)  # 0: 추상, 1: 구체적, 2: 측정값 기반
    tag_value = Column(String(20))  # 2차 태그만: "긴", "보통", "짧은" (0,1차는 NULL)

    # 관계
    profile = relationship("PoolProfile", back_populates="tags")

    def to_dict(self):
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'tag_name': self.tag_name,
            'tag_level': self.tag_level,
            'tag_value': self.tag_value
        }


class PoolLandmark(Base):
    """풀 랜드마크 좌표 테이블"""
    __tablename__ = 'pool_landmarks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('pool_profiles.id'), nullable=False)
    mp_idx = Column(Integer, nullable=False)  # MediaPipe 인덱스 (0~491, 500)
    x = Column(Numeric(10, 3), nullable=False)  # X 좌표 (소수점 3자리)
    y = Column(Numeric(10, 3), nullable=False)  # Y 좌표 (소수점 3자리)
    z = Column(Numeric(10, 3))                  # Z 좌표 (소수점 3자리, 있는 경우)

    # 관계
    profile = relationship("PoolProfile", back_populates="landmarks_points")

    def to_dict(self):
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'mp_idx': self.mp_idx,
            'x': self.x,
            'y': self.y,
            'z': self.z
        }


class Pool2ndTagDef(Base):
    """풀 2차 태그 정의 테이블"""
    __tablename__ = 'pool_2nd_tag_def'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(100), unique=True, nullable=False)
    measurement_type = Column(String(20), nullable=False)  # "길이", "비율", "곡률"
    description = Column(Text)

    # 거리 계산 타입 (길이/비율 공통)
    거리계산방식 = Column(String(20))  # "직선거리", "x좌표거리", "y좌표거리"

    # 분자 (길이 측정일 때는 이것만 사용, 비율일 때는 분자)
    분자_점1 = Column(Integer)
    분자_점2 = Column(Integer)

    # 분모 (길이 측정일 때는 NULL, 비율일 때만 사용)
    분모_점1 = Column(Integer)
    분모_점2 = Column(Integer)

    # 곡률 측정용 (곡률일 때만 사용)
    곡률점리스트 = Column(JSON)

    def to_dict(self):
        return {
            'id': self.id,
            'tag_name': self.tag_name,
            'measurement_type': self.measurement_type,
            'description': self.description,
            '거리계산방식': self.거리계산방식,
            '분자_점1': self.분자_점1,
            '분자_점2': self.분자_점2,
            '분모_점1': self.분모_점1,
            '분모_점2': self.분모_점2,
            '곡률점리스트': self.곡률점리스트
        }


class PoolTagThreshold(Base):
    """풀 태그 임계값 정의 테이블"""
    __tablename__ = 'pool_tag_thresholds'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(50), nullable=False)  # "eye-길이", "nose-크기" 등
    value_name = Column(String(20), nullable=False)  # "긴", "보통", "짧은"
    min_threshold = Column(Float)  # 최소 임계값
    max_threshold = Column(Float)  # 최대 임계값

    def to_dict(self):
        return {
            'id': self.id,
            'tag_name': self.tag_name,
            'value_name': self.value_name,
            'min_threshold': self.min_threshold,
            'max_threshold': self.max_threshold
        }


class Pool2ndTagValue(Base):
    """풀 2차 태그 측정값 테이블"""
    __tablename__ = 'pool_2nd_tag_values'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('pool_profiles.id'), nullable=False)
    tag_name = Column(String(100), nullable=False)  # "eye-길이", "nose-콧볼" 등
    측정값 = Column(Float, nullable=True)  # 실제 계산된 값 (계산 불가시 NULL)

    # 관계
    profile = relationship("PoolProfile", back_populates="measurement_values")

    def to_dict(self):
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'tag_name': self.tag_name,
            '측정값': self.측정값
        }


# ==================== User Domain Models ====================

class UserProfile(Base):
    """유저 프로필 테이블 - 회원 정보"""
    __tablename__ = 'user_profiles'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)              # 이름
    login_id = Column(String(50), unique=True, nullable=False)  # 로그인 ID
    password = Column(String(255), nullable=False)          # 비밀번호 (해시)
    email = Column(String(255), unique=True)                # 이메일
    age = Column(Integer)                                   # 나이
    gender = Column(String(10))                             # 성별
    created_at = Column(DateTime, default=datetime.utcnow)  # 가입 날짜
    json_file_path = Column(String(500))                    # JSON 파일 경로
    image_file_path = Column(String(500))                   # 얼굴 이미지 경로

    # 관계
    tags = relationship("UserTag", back_populates="user", cascade="all, delete-orphan")
    landmarks_points = relationship("UserLandmark", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self, include_password=False):
        """딕셔너리로 변환"""
        result = {
            'user_id': self.user_id,
            'name': self.name,
            'login_id': self.login_id,
            'email': self.email,
            'age': self.age,
            'gender': self.gender,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'json_file_path': self.json_file_path,
            'image_file_path': self.image_file_path,
            'tags': [tag.tag_name for tag in self.tags]
        }

        # 비밀번호는 기본적으로 반환하지 않음 (보안)
        if include_password:
            result['password'] = self.password

        # landmarks가 있으면 포함
        if self.landmarks_points:
            result['landmarks'] = [lm.to_dict() for lm in self.landmarks_points]
        else:
            result['landmarks'] = None

        return result


class UserLandmark(Base):
    """유저 랜드마크 좌표 테이블"""
    __tablename__ = 'user_landmarks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id'), nullable=False)
    mp_idx = Column(Integer, nullable=False)
    x = Column(Numeric(10, 3), nullable=False)
    y = Column(Numeric(10, 3), nullable=False)
    z = Column(Numeric(10, 3))

    # 관계
    user = relationship("UserProfile", back_populates="landmarks_points")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'mp_idx': self.mp_idx,
            'x': self.x,
            'y': self.y,
            'z': self.z
        }


class UserTag(Base):
    """유저 태그 테이블"""
    __tablename__ = 'user_tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id'), nullable=False)
    tag_name = Column(String(100), nullable=False)
    tag_level = Column(Integer, nullable=False)  # 0: 추상, 1: 구체적, 2: 측정값 기반
    tag_value = Column(String(20))  # 2차 태그만: "긴", "보통", "짧은"

    # 관계
    user = relationship("UserProfile", back_populates="tags")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'tag_name': self.tag_name,
            'tag_level': self.tag_level,
            'tag_value': self.tag_value
        }


# ==================== Pool Tag Relation ====================

class PoolTagRelation(Base):
    """풀 태그 계층 관계 테이블 - 하위 태그 조합이 상위 태그를 정의"""
    __tablename__ = 'pool_tag_relation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_tags = Column(JSON, nullable=False)      # 상위 태그들 (배열)
    child_tags = Column(JSON, nullable=False)       # 하위 태그들 (배열)
    parent_level = Column(Integer, nullable=False)  # parent가 몇 차? 0 or 1

    def to_dict(self):
        return {
            'id': self.id,
            'parent_tags': self.parent_tags,
            'child_tags': self.child_tags,
            'parent_level': self.parent_level
        }