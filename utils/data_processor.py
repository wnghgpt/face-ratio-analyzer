"""
JSON 파일 처리 및 데이터 파싱 유틸리티
"""
import json
import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def load_json_files(folder_path: str) -> List[Dict]:
    """
    폴더에서 모든 JSON 파일을 로드

    Args:
        folder_path: JSON 파일들이 있는 폴더 경로

    Returns:
        JSON 데이터 리스트
    """
    files_data = []
    folder = Path(folder_path)

    if not folder.exists():
        return files_data

    for file_path in folder.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 파일명 정보 추가
                data['_filename'] = file_path.name
                files_data.append(data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue

    return files_data


def parse_face_ratio(ratio_str: str) -> Tuple[float, float, float]:
    """
    얼굴 비율 문자열을 파싱

    Args:
        ratio_str: "1:1.2:0.8" 형태의 비율 문자열

    Returns:
        (첫번째, 두번째, 세번째) 비율 값 튜플
    """
    try:
        if ":" in ratio_str:
            parts = ratio_str.split(":")
            if len(parts) >= 3:
                return float(parts[0]), float(parts[1]), float(parts[2])
            elif len(parts) == 2:
                return float(parts[0]), float(parts[1]), 1.0

        # 단일 값인 경우
        val = float(ratio_str)
        return 1.0, val, 1.0

    except (ValueError, AttributeError):
        # 파싱 실패 시 기본값
        return 1.0, 1.0, 1.0


def process_json_data(json_data: List[Dict]) -> pd.DataFrame:
    """
    JSON 데이터를 분석용 DataFrame으로 변환

    Args:
        json_data: JSON 데이터 리스트

    Returns:
        처리된 pandas DataFrame
    """
    if not json_data:
        return pd.DataFrame()

    processed_data = []

    for data in json_data:
        try:
            # 기본 정보 추출
            name = data.get('name', 'unknown')
            tags = data.get('tags', [])
            face_ratio = data.get('faceRatio', '1:1:1')
            roll_angle = data.get('rollAngle', 0)
            filename = data.get('_filename', 'unknown.json')

            # 비율 파싱
            ratio_1, ratio_2, ratio_3 = parse_face_ratio(face_ratio)

            # 태그 문자열 생성
            tags_str = ', '.join(tags) if isinstance(tags, list) else str(tags)

            processed_data.append({
                'name': name,
                'filename': filename,
                'tags': tags_str,
                'tags_list': tags if isinstance(tags, list) else [],
                'face_ratio_str': face_ratio,
                'ratio_1': ratio_1,
                'ratio_2': ratio_2,  # X축 용
                'ratio_3': ratio_3,  # Y축 용
                'x_axis': ratio_2,   # X축 (두번째 값)
                'y_axis': ratio_3,   # Y축 (세번째 값)
                'roll_angle': roll_angle,
                'data_source': 'analysis'
            })

        except Exception as e:
            print(f"Error processing data for {data.get('name', 'unknown')}: {e}")
            continue

    return pd.DataFrame(processed_data)


def get_available_files(folder_path: str) -> List[str]:
    """
    폴더에서 사용 가능한 JSON 파일 목록 반환

    Args:
        folder_path: 폴더 경로

    Returns:
        파일명 리스트
    """
    folder = Path(folder_path)
    if not folder.exists():
        return []

    return [f.name for f in folder.glob("*.json")]


def validate_json_structure(data: Dict) -> Tuple[bool, str]:
    """
    JSON 데이터 구조 검증

    Args:
        data: JSON 데이터

    Returns:
        (유효한지 여부, 오류 메시지)
    """
    required_fields = ['name', 'faceRatio']

    for field in required_fields:
        if field not in data:
            return False, f"Required field '{field}' is missing"

    # 비율 데이터 검증
    try:
        parse_face_ratio(data['faceRatio'])
    except:
        return False, f"Invalid faceRatio format: {data.get('faceRatio')}"

    return True, "Valid"