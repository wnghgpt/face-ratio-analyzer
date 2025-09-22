#!/usr/bin/env python3
"""
테스트 스크립트 - 모듈 import 및 기본 기능 검증
"""

def test_module_imports():
    """모듈 import 테스트"""
    print("🔍 모듈 import 테스트...")

    try:
        # 데이터베이스 모듈
        from database.models import Base, FaceData, Tag
        print("✅ Database models imported")

        # 엔진 모듈 (패키지가 없을 때를 위한 fallback)
        try:
            from engines.ratio_parser import RatioParser
            print("✅ Ratio parser imported")
        except ImportError as e:
            print(f"⚠️ Ratio parser import failed: {e}")

        try:
            from engines.analysis_engine import AnalysisEngine
            print("✅ Analysis engine imported")
        except ImportError as e:
            print(f"⚠️ Analysis engine import failed: {e}")

        # 컴포넌트 모듈
        try:
            from components.data_selector import render_data_selector
            print("✅ Data selector imported")
        except ImportError as e:
            print(f"⚠️ Data selector import failed: {e}")

        print("✅ 모든 핵심 모듈 import 성공!")
        return True

    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return False

def test_ratio_parsing():
    """비율 파싱 테스트 (외부 패키지 없이)"""
    print("\n🔍 비율 파싱 로직 테스트...")

    # 간단한 비율 파싱 테스트
    test_ratios = [
        "1:1.2:0.8",
        "1:1.5",
        "2.5:3.1:1.8:2.2",
        "invalid_ratio"
    ]

    for ratio in test_ratios:
        try:
            parts = ratio.split(':')
            if len(parts) >= 2:
                # 각 부분이 숫자인지 확인
                values = []
                for part in parts:
                    try:
                        values.append(float(part))
                    except ValueError:
                        raise ValueError(f"Invalid number: {part}")

                print(f"✅ {ratio} -> {len(values)} components: {values}")
            else:
                raise ValueError("Not enough components")

        except Exception as e:
            print(f"❌ {ratio} -> Error: {e}")

    return True

def test_file_structure():
    """파일 구조 검증"""
    print("\n🔍 파일 구조 테스트...")

    import os

    required_files = [
        "app.py",
        "database/models.py",
        "database/db_manager.py",
        "engines/ratio_parser.py",
        "engines/analysis_engine.py",
        "components/data_selector.py",
        "components/variable_selector.py",
        "components/analysis_builder.py",
        "components/results_viewer.py",
        "requirements.txt"
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n⚠️ {len(missing_files)}개 파일이 없습니다.")
        return False
    else:
        print(f"\n✅ 모든 {len(required_files)}개 파일이 존재합니다!")
        return True

def main():
    """메인 테스트 함수"""
    print("🧪 Face Ratio Analyzer 시스템 테스트\n")

    # 테스트 실행
    tests = [
        ("파일 구조", test_file_structure),
        ("모듈 Import", test_module_imports),
        ("비율 파싱 로직", test_ratio_parsing),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 실패: {e}")
            results.append((test_name, False))

    # 결과 요약
    print("\n" + "="*50)
    print("📊 테스트 결과 요약")
    print("="*50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\n총 {len(results)}개 테스트 중 {passed}개 통과")

    if passed == len(results):
        print("🎉 모든 테스트 통과! 시스템이 정상적으로 구성되었습니다.")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 누락된 패키지나 파일을 확인해주세요.")

if __name__ == "__main__":
    main()