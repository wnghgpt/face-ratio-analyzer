#!/usr/bin/env python3
"""
데이터베이스 스키마 자동 관리
"""
import os
import sys
from sqlalchemy import text

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connect_db import db_manager
from database.schema_def import Base, Pool2ndTagDef, PoolTagThreshold, PoolTagRelation
import json

class SchemaManager:
    def __init__(self):
        self.engine = db_manager.engine

    def create_all_tables(self):
        """모든 테이블 자동 생성"""
        print("🔧 데이터베이스 스키마 생성 중...")

        try:
            # SQLAlchemy 모델 기반으로 모든 테이블 생성
            Base.metadata.create_all(bind=self.engine)
            print("✅ 모든 테이블 생성 완료")

            # 생성된 테이블 확인
            with db_manager.get_session() as session:
                result = session.execute(text("SHOW TABLES")).fetchall()
                tables = [row[0] for row in result]
                print(f"📋 생성된 테이블: {', '.join(tables)}")

        except Exception as e:
            print(f"❌ 테이블 생성 실패: {e}")
            return False

        return True

    def drop_unused_tables(self):
        """사용하지 않는 테이블 삭제"""
        print("🗑️ 불필요한 테이블 삭제 중...")

        # 기존 테이블명들 삭제
        old_tables = [
            'analysis_configs',
            'analysis_results',
            'custom_variables',
            'face_data',
            'face_basic_measurements',
            'landmarks',
            'tags',
            'tag_measurement_definitions',
            'tag_thresholds',
            'face_measurement_values',
            'pool_tag_relation'  # 스키마 변경으로 재생성 필요
        ]

        try:
            with db_manager.get_session() as session:
                for table in old_tables:
                    try:
                        session.execute(text(f"DROP TABLE IF EXISTS {table}"))
                        print(f"   ✅ {table} 삭제됨")
                    except Exception as e:
                        print(f"   ⚠️ {table} 삭제 실패: {e}")

                session.commit()

        except Exception as e:
            print(f"❌ 테이블 삭제 실패: {e}")
            return False

        return True

    def initialize_measurement_definitions(self):
        """측정 정의 초기 데이터 로드"""
        print("📊 측정 정의 초기화 중...")

        json_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'source_data', 'measurement_definitions.json'
        )

        if not os.path.exists(json_file):
            print(f"⚠️ JSON 파일 없음: {json_file}")
            return True

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                definitions = json.load(f)

            with db_manager.get_session() as session:
                # 기존 데이터 확인
                existing_count = session.query(Pool2ndTagDef).count()

                if existing_count > 0:
                    print(f"📋 기존 측정 정의 {existing_count}개 존재")
                    return True

                # 새 데이터 추가
                for definition in definitions:
                    new_def = Pool2ndTagDef(
                        tag_name=definition['tag_name'],
                        measurement_type=definition['measurement_type'],
                        description=definition.get('description'),
                        거리계산방식=definition.get('거리계산방식'),
                        분자_점1=definition.get('분자_점1'),
                        분자_점2=definition.get('분자_점2'),
                        분모_점1=definition.get('분모_점1'),
                        분모_점2=definition.get('분모_점2'),
                        곡률점리스트=definition.get('곡률점리스트')
                    )
                    session.add(new_def)

                session.commit()

                final_count = session.query(Pool2ndTagDef).count()
                print(f"✅ {final_count}개 측정 정의 로드 완료")

        except Exception as e:
            print(f"❌ 측정 정의 초기화 실패: {e}")
            return False

        return True

    def initialize_threshold_definitions(self):
        """임계값 정의 초기 데이터 로드"""
        print("📏 임계값 정의 초기화 중...")

        json_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'source_data', 'threshold_definitions.json'
        )

        if not os.path.exists(json_file):
            print(f"⚠️ JSON 파일 없음: {json_file}")
            return True

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                thresholds = json.load(f)

            with db_manager.get_session() as session:
                # 기존 데이터 확인
                existing_count = session.query(PoolTagThreshold).count()

                if existing_count > 0:
                    print(f"📋 기존 임계값 정의 {existing_count}개 존재")
                    return True

                # 새 데이터 추가
                for threshold in thresholds:
                    new_threshold = PoolTagThreshold(
                        tag_name=threshold['tag_name'],
                        value_name=threshold['value_name'],
                        min_threshold=threshold.get('min_threshold'),
                        max_threshold=threshold.get('max_threshold')
                    )
                    session.add(new_threshold)

                session.commit()

                final_count = session.query(PoolTagThreshold).count()
                print(f"✅ {final_count}개 임계값 정의 로드 완료")

        except Exception as e:
            print(f"❌ 임계값 정의 초기화 실패: {e}")
            return False

        return True

    def initialize_tag_relations(self):
        """태그 관계 정의 초기 데이터 로드"""
        print("🔗 태그 관계 정의 초기화 중...")

        json_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'source_data', 'tag_relations.json'
        )

        if not os.path.exists(json_file):
            print(f"⚠️ JSON 파일 없음: {json_file}")
            return True

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                relations = json.load(f)

            with db_manager.get_session() as session:
                # 기존 데이터 확인
                existing_count = session.query(PoolTagRelation).count()

                if existing_count > 0:
                    print(f"📋 기존 태그 관계 {existing_count}개 존재")
                    return True

                # 새 데이터 추가
                for relation in relations:
                    new_relation = PoolTagRelation(
                        parent_tags=relation['parent_tags'],
                        child_tags=relation['child_tags'],
                        parent_level=relation['parent_level']
                    )
                    session.add(new_relation)

                session.commit()

                final_count = session.query(PoolTagRelation).count()
                print(f"✅ {final_count}개 태그 관계 로드 완료")

        except Exception as e:
            print(f"❌ 태그 관계 초기화 실패: {e}")
            return False

        return True

    def setup_database(self):
        """전체 데이터베이스 설정"""
        print("🚀 데이터베이스 전체 설정 시작")
        print("=" * 50)

        success = True

        # 1. 불필요한 테이블 삭제
        if not self.drop_unused_tables():
            success = False

        # 2. 모든 테이블 생성
        if not self.create_all_tables():
            success = False

        # 3. 측정 정의 초기화
        if not self.initialize_measurement_definitions():
            success = False

        # 4. 임계값 정의 초기화
        if not self.initialize_threshold_definitions():
            success = False

        # 5. 태그 관계 초기화
        if not self.initialize_tag_relations():
            success = False

        if success:
            print("\n🎉 데이터베이스 설정 완료!")
        else:
            print("\n❌ 설정 중 일부 오류 발생")

        return success

def main():
    """메인 함수"""
    manager = SchemaManager()
    manager.setup_database()

if __name__ == "__main__":
    main()