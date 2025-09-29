#!/usr/bin/env python3
"""
JSON 파일에서 측정 정의를 읽어서 데이터베이스에 로드하는 스크립트
"""
import os
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager
from database.models import TagMeasurementDefinition

def load_measurement_definitions():
    """JSON 파일에서 측정 정의 로드"""
    json_file = Path(__file__).parent / "database" / "measurement_definitions.json"

    if not json_file.exists():
        print(f"❌ JSON 파일을 찾을 수 없습니다: {json_file}")
        return False

    print(f"📖 측정 정의 로드 중: {json_file}")

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            definitions = json.load(f)

        print(f"🔍 {len(definitions)}개의 정의 발견")

        with db_manager.get_session() as session:
            # 기존 데이터 삭제 (재로드)
            session.query(TagMeasurementDefinition).delete()

            added_count = 0
            for definition in definitions:
                try:
                    # 새 정의 생성
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
                    added_count += 1
                    print(f"  ✅ {definition['tag_name']} ({definition['measurement_type']})")

                except Exception as e:
                    print(f"  ❌ {definition.get('tag_name', 'Unknown')}: {e}")
                    continue

            session.commit()
            print(f"\n🎉 {added_count}개 정의 로드 완료!")

            # 결과 확인
            total = session.query(TagMeasurementDefinition).count()
            print(f"📊 총 정의 수: {total}개")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 로드 실패: {e}")
        return False

def show_definitions():
    """현재 저장된 정의들 출력"""
    print("\n📋 현재 저장된 측정 정의들:")
    print("=" * 60)

    with db_manager.get_session() as session:
        definitions = session.query(TagMeasurementDefinition).all()

        if not definitions:
            print("📭 저장된 정의가 없습니다.")
            return

        for definition in definitions:
            print(f"\n🏷️  {definition.tag_name} ({definition.measurement_type})")
            print(f"   📝 {definition.description}")

            if definition.measurement_type == "길이":
                print(f"   📏 점1: {definition.point1_mpidx}, 점2: {definition.point2_mpidx}")
            elif definition.measurement_type == "비율":
                print(f"   🔢 분모: {definition.denominator_point1}-{definition.denominator_point2}")
                print(f"      분자: {definition.numerator_point1}-{definition.numerator_point2}")
            elif definition.measurement_type == "곡률":
                print(f"   🌊 점들: {definition.curvature_points}")

def main():
    """메인 함수"""
    print("🎯 측정 정의 관리")
    print("=" * 40)

    # JSON 파일에서 로드
    if load_measurement_definitions():
        # 결과 확인
        show_definitions()

        print(f"\n💡 JSON 파일 편집 방법:")
        print(f"   📝 {Path(__file__).parent / 'json_files' / 'measurement_definitions.json'}")
        print(f"   🔄 편집 후 이 스크립트 재실행하면 자동 동기화")
    else:
        print(f"\n❌ 로드 실패")

if __name__ == "__main__":
    main()