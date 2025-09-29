#!/usr/bin/env python3
"""
JSON 파일들의 태그를 새로운 태그 체계로 업데이트하는 스크립트
"""
import json
import os
import glob
from typing import List, Dict, Any

def get_tag_mappings() -> Dict[str, str]:
    """기존 태그를 새로운 태그로 매핑하는 딕셔너리"""
    return {
        # 추상 태그 수정
        "믿음직한": "선한",

        # 1차 인상 태그 수정
        "이국적인": "서구적인",
        "시원시원한": "진한",

        # 삭제할 태그들 (빈 문자열로 매핑하면 제거됨)
        "고집있는": "",
        "서글서글한": "",

        # 2차 세부특성 - 눈에서 삭제할 것들
        "eye-크기-큰": "",
        "eye-크기-보통": "",
        "eye-크기-작은": "",
        "eye-동공-사백안": "",
        "eye-동공-보통": "",
        "eye-동공-삼백안": "",
        "eye-동공-반가려짐": "",

        # 입술 두께 변경 - 기존 3단계를 4단계로
        "mouth-두께-두꺼운": "mouth-두께-두꺼운",  # 유지
        "mouth-두께-보통": "mouth-두께-도톰",      # 보통 -> 도톰
        "mouth-두께-얇은": "mouth-두께-얇은",      # 유지
        # 새로 추가될 "mouth-두께-보통"은 수동으로 추가 필요

        # 입술 긴장도 삭제
        "mouth-위긴장도-있음": "",
        "mouth-위긴장도-보통": "",
        "mouth-위긴장도-없음": "",
        "mouth-아래긴장도-있음": "",
        "mouth-아래긴장도-보통": "",
        "mouth-아래긴장도-없음": "",

        # 콧구멍 태그 변경
        "nose-콧구멍-넓은": "nose-콧구멍-큰",
        "nose-콧구멍-좁은": "nose-콧구멍-작은",

        # 턱 태그 변경 (앞턱 -> 턱형태)
        "silhouette-턱-발달-발달": "silhouette-턱형태-발달",
        "silhouette-턱-발달-보통": "silhouette-턱형태-보통",
        "silhouette-턱-발달-무턱": "silhouette-턱형태-무턱",
        "silhouette-턱-형태-뾰족한": "silhouette-턱형태-뾰족",
        "silhouette-턱-형태-보통": "silhouette-턱형태-보통",
        "silhouette-턱-형태-각진": "silhouette-턱형태-뾰족",  # 각진 -> 뾰족으로 통합

        # 윤곽에서 삭제할 것들
        "silhouette-옆광대-크기-큰": "",
        "silhouette-옆광대-크기-보통": "",
        "silhouette-옆광대-크기-작은": "",
        "silhouette-볼-탄력-쳐진": "",
        "silhouette-볼-탄력-보통": "",
        "silhouette-볼-탄력-탄력": "",
    }

def get_additional_animal_tags() -> List[str]:
    """새로 추가될 동물상 태그들"""
    return ["토끼", "꼬부기", "사막여우", "호랑이"]

def update_tags(tags: List[str], tag_mappings: Dict[str, str]) -> List[str]:
    """태그 리스트를 새로운 태그 체계로 업데이트"""
    updated_tags = []

    for tag in tags:
        if tag in tag_mappings:
            new_tag = tag_mappings[tag]
            if new_tag:  # 빈 문자열이 아니면 추가
                updated_tags.append(new_tag)
            # 빈 문자열이면 삭제 (추가하지 않음)
        else:
            # 매핑되지 않은 태그는 그대로 유지
            updated_tags.append(tag)

    # 중복 제거
    return list(dict.fromkeys(updated_tags))

def update_json_file(file_path: str, tag_mappings: Dict[str, str]) -> bool:
    """단일 JSON 파일 업데이트"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'tags' in data and isinstance(data['tags'], list):
            original_count = len(data['tags'])
            data['tags'] = update_tags(data['tags'], tag_mappings)
            updated_count = len(data['tags'])

            # 백업 생성
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 원본 파일 업데이트
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ {os.path.basename(file_path)}: {original_count} -> {updated_count} tags")
            return True
        else:
            print(f"⚠️  {os.path.basename(file_path)}: No 'tags' field found")
            return False

    except Exception as e:
        print(f"❌ {os.path.basename(file_path)}: Error - {e}")
        return False

def main():
    """메인 함수"""
    print("🏷️  태그 시스템 업데이트 시작...")

    # 설정
    json_dir = "/home/web_app/face-ratio-analyzer/json_files"
    tag_mappings = get_tag_mappings()

    # processed 폴더 제외하고 JSON 파일 찾기
    json_files = []
    for file_path in glob.glob(os.path.join(json_dir, "*.json")):
        if "processed" not in file_path:
            json_files.append(file_path)

    print(f"📁 총 {len(json_files)}개 파일 발견")
    print(f"🔄 적용할 태그 변경사항: {len([k for k, v in tag_mappings.items() if v])}개")
    print(f"🗑️  삭제할 태그: {len([k for k, v in tag_mappings.items() if not v])}개")

    # 각 파일 업데이트
    success_count = 0
    for file_path in json_files:
        if update_json_file(file_path, tag_mappings):
            success_count += 1

    print(f"\n✨ 완료: {success_count}/{len(json_files)} 파일 업데이트됨")
    print("📋 변경사항 요약:")
    print("   - 믿음직한 → 선한")
    print("   - 이국적인 → 서구적인")
    print("   - 시원시원한 → 진한")
    print("   - 동물상에 토끼, 꼬부기, 사막여우, 호랑이 추가 가능")
    print("   - 입술 두께 4단계로 변경 (두꺼운-도톰-보통-얇은)")
    print("   - 입술 중심 추가 (위/중간/아래)")
    print("   - 턱 발달/형태 → 턱형태로 통합")
    print("   - 콧구멍 크기 용어 변경")
    print("   - 불필요한 태그들 삭제 (긴장도, 동공, 눈크기, 옆광대크기, 볼탄력)")
    print(f"💾 백업 파일들이 .backup 확장자로 생성되었습니다")

if __name__ == "__main__":
    main()