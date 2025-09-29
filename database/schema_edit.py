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
from database.schema_def import Base, TagMeasurementDefinition
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

        unused_tables = [
            'analysis_configs',
            'analysis_results',
            'custom_variables'
        ]

        try:
            with db_manager.get_session() as session:
                for table in unused_tables:
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
                existing_count = session.query(TagMeasurementDefinition).count()

                if existing_count > 0:
                    print(f"📋 기존 측정 정의 {existing_count}개 존재")
                    return True

                # 새 데이터 추가
                for definition in definitions:
                    new_def = TagMeasurementDefinition(
                        tag_name=definition['tag_name'],
                        measurement_type=definition['measurement_type'],
                        description=definition.get('description'),
                        point1_mpidx=definition.get('point1_mpidx'),
                        point2_mpidx=definition.get('point2_mpidx'),
                        denominator_point1=definition.get('denominator_point1'),
                        denominator_point2=definition.get('denominator_point2'),
                        numerator_point1=definition.get('numerator_point1'),
                        numerator_point2=definition.get('numerator_point2'),
                        curvature_points=definition.get('curvature_points')
                    )
                    session.add(new_def)

                session.commit()

                final_count = session.query(TagMeasurementDefinition).count()
                print(f"✅ {final_count}개 측정 정의 로드 완료")

        except Exception as e:
            print(f"❌ 측정 정의 초기화 실패: {e}")
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