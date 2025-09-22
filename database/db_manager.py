"""
데이터베이스 매니저
"""
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .models import Base, FaceData, Tag, CustomVariable, AnalysisConfig, AnalysisResult
import hashlib
import json
from datetime import datetime
import os


class DatabaseManager:
    def __init__(self, db_path="database/face_analytics.db"):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 데이터베이스 초기화
        self.init_database()

    def init_database(self):
        """데이터베이스 테이블 생성"""
        # 디렉토리 생성
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # 테이블 생성
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self):
        """세션 컨텍스트 매니저"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def import_json_data(self, json_data_list):
        """JSON 데이터를 데이터베이스로 임포트"""
        from engines.ratio_parser import RatioParser

        parser = RatioParser()

        with self.get_session() as session:
            for json_data in json_data_list:
                try:
                    # 기존 데이터 체크 (이름 기준)
                    existing = session.query(FaceData).filter_by(name=json_data.get('name')).first()
                    if existing:
                        continue  # 이미 존재하면 스킵

                    # 비율 파싱
                    ratio_components = parser.parse_ratio_to_components(json_data.get('faceRatio', ''))

                    # FaceData 객체 생성
                    face_data = FaceData(
                        name=json_data.get('name', 'unknown'),
                        face_ratio_raw=json_data.get('faceRatio', ''),
                        ratio_1=ratio_components.get('ratio_1'),
                        ratio_2=ratio_components.get('ratio_2'),
                        ratio_3=ratio_components.get('ratio_3'),
                        ratio_4=ratio_components.get('ratio_4'),
                        ratio_5=ratio_components.get('ratio_5'),
                        ratio_2_1=ratio_components.get('ratio_2_1'),
                        ratio_3_1=ratio_components.get('ratio_3_1'),
                        ratio_3_2=ratio_components.get('ratio_3_2'),
                        roll_angle=json_data.get('rollAngle', 0),
                        ratios_detail=json.dumps(json_data.get('ratios', {})),
                        landmarks=json.dumps(json_data.get('landmarks', [])),
                        meta_data=json.dumps({
                            'source_file': json_data.get('_filename', ''),
                            'import_date': datetime.utcnow().isoformat()
                        })
                    )

                    session.add(face_data)
                    session.flush()  # ID 생성을 위해

                    # 태그 추가
                    tags = json_data.get('tags', [])
                    if isinstance(tags, str):
                        tags = [tag.strip() for tag in tags.split(',')]

                    for tag_name in tags:
                        if tag_name.strip():
                            tag = Tag(face_data_id=face_data.id, tag_name=tag_name.strip())
                            session.add(tag)

                except Exception as e:
                    print(f"Error importing {json_data.get('name', 'unknown')}: {e}")
                    continue

    def query_data(self, filters=None):
        """데이터 쿼리"""
        with self.get_session() as session:
            query = session.query(FaceData)

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
                    query = query.filter(FaceData.ratio_2.between(min_val, max_val))

                if 'ratio_y_range' in filters and filters['ratio_y_range']:
                    min_val, max_val = filters['ratio_y_range']
                    query = query.filter(FaceData.ratio_3.between(min_val, max_val))

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

        # 커스텀 변수들 추가
        with self.get_session() as session:
            custom_vars = session.query(CustomVariable.variable_name).distinct().all()
            custom_var_names = [var[0] for var in custom_vars]

        return base_vars + custom_var_names

    def save_analysis_config(self, name, description, config, tags=None):
        """분석 설정 저장"""
        with self.get_session() as session:
            analysis_config = AnalysisConfig(
                name=name,
                description=description,
                config_json=json.dumps(config),
                tags=','.join(tags) if tags else '',
                created_date=datetime.utcnow()
            )
            session.add(analysis_config)
            return analysis_config.id

    def load_analysis_config(self, config_id):
        """분석 설정 로드"""
        with self.get_session() as session:
            config = session.query(AnalysisConfig).filter_by(id=config_id).first()
            if config:
                # 사용 횟수 증가
                config.use_count += 1
                config.last_used = datetime.utcnow()
                return config.to_dict()
            return None

    def get_analysis_configs(self, tags=None, search=None):
        """저장된 분석 설정들 조회"""
        with self.get_session() as session:
            query = session.query(AnalysisConfig)

            if tags:
                # 태그 필터링
                for tag in tags:
                    query = query.filter(AnalysisConfig.tags.like(f'%{tag}%'))

            if search:
                # 이름이나 설명에서 검색
                query = query.filter(
                    (AnalysisConfig.name.like(f'%{search}%')) |
                    (AnalysisConfig.description.like(f'%{search}%'))
                )

            # 사용 횟수 순으로 정렬
            query = query.order_by(AnalysisConfig.use_count.desc())

            configs = query.all()
            return [config.to_dict() for config in configs]

    def cache_analysis_result(self, config, result_data):
        """분석 결과 캐시"""
        config_hash = hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest()

        with self.get_session() as session:
            # 기존 캐시 삭제
            session.query(AnalysisResult).filter_by(config_hash=config_hash).delete()

            # 새 캐시 저장
            cache_entry = AnalysisResult(
                config_hash=config_hash,
                result_data=json.dumps(result_data),
                created_date=datetime.utcnow(),
                file_count=len(result_data.get('data', []))
            )
            session.add(cache_entry)

    def get_cached_result(self, config):
        """캐시된 분석 결과 조회"""
        config_hash = hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest()

        with self.get_session() as session:
            cache_entry = session.query(AnalysisResult).filter_by(config_hash=config_hash).first()
            if cache_entry:
                return cache_entry.to_dict()
            return None

    def get_stats(self):
        """데이터베이스 통계"""
        with self.get_session() as session:
            total_records = session.query(FaceData).count()
            total_tags = session.query(Tag.tag_name).distinct().count()
            total_configs = session.query(AnalysisConfig).count()

            return {
                'total_records': total_records,
                'total_unique_tags': total_tags,
                'total_saved_configs': total_configs
            }

# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()