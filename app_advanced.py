"""
Face Coordinate Analyzer
실시간 좌표 계산 기반 얼굴 분석 플랫폼
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
from pathlib import Path

# Database and engines
from database.db_manager import db_manager

# Page config
st.set_page_config(
    page_title="Face Coordinate Analyzer",
    page_icon="🎭",
    layout="wide"
)

def main():
    st.title("🎭 Face Coordinate Analyzer")
    st.markdown("**실시간 좌표 계산 기반 얼굴 분석 플랫폼**")

    # 좌표 분석만 렌더링
    render_landmarks_analysis_tab()


def render_landmarks_analysis_tab():
    """새로운 좌표 분석 탭 - 길이 기반 단순화 버전"""
    st.header("🧮 좌표 분석 (실시간 계산)")
    st.markdown("두 거리를 기반으로 한 비교 분석")

    # 랜드마크 데이터 로드
    landmarks_data = load_landmarks_data()
    if landmarks_data.empty:
        st.warning("💡 landmarks가 포함된 JSON 파일이 필요합니다.")
        return

    st.sidebar.success(f"📍 {len(landmarks_data)}개 데이터 로드됨")

    # 1. 계산 목적 선택 (단순화)
    st.sidebar.write("### 1. 계산 목적")
    purpose = st.sidebar.selectbox(
        "분석 목적을 선택하세요:",
        ["📏 거리 측정", "⚖️ 비율 계산"],
        index=1
    )

    # 2. 길이1 설정
    st.sidebar.write("### 2. 길이1 설정(x축)")
    col1, col2, col3 = st.sidebar.columns([1, 1, 1.2])

    with col1:
        length1_point1 = st.number_input(
            "점1",
            min_value=0,
            max_value=491,
            value=33,  # 왼쪽 눈 중심
            key="length1_point1"
        )

    with col2:
        length1_point2 = st.number_input(
            "점2",
            min_value=0,
            max_value=491,
            value=133,  # 오른쪽 눈 중심
            key="length1_point2"
        )

    with col3:
        length1_calc = st.selectbox(
            "계산",
            ["직선거리", "X좌표거리", "Y좌표거리"],
            key="length1_calc"
        )

    # 3. 길이2 설정 (비율 계산일 때만 표시)
    if purpose == "⚖️ 비율 계산":
        st.sidebar.write("### 3. 길이2 설정(y축)")
        col1, col2, col3 = st.sidebar.columns([1, 1, 1.2])

        with col1:
            length2_point1 = st.number_input(
                "점1",
                min_value=0,
                max_value=491,
                value=48,  # 왼쪽 입꼬리
                key="length2_point1"
            )

        with col2:
            length2_point2 = st.number_input(
                "점2",
                min_value=0,
                max_value=491,
                value=54,  # 오른쪽 입꼬리
                key="length2_point2"
            )

        with col3:
            length2_calc = st.selectbox(
                "계산",
                ["직선거리", "X좌표거리", "Y좌표거리"],
                key="length2_calc"
            )
    else:
        # 거리 측정일 때는 기본값 설정
        length2_point1 = 48
        length2_point2 = 54
        length2_calc = "직선거리"

    # 4. 차트 옵션 (비율 계산일 때만)
    normalize_ratio = False
    swap_axes = False
    if purpose == "⚖️ 비율 계산":
        st.sidebar.write("### 📊 차트 옵션")
        normalize_ratio = st.sidebar.checkbox("📏 X축을 1로 정규화",
                                            value=True,
                                            help="길이1을 1로 고정하고 길이2를 그에 맞게 스케일링합니다. 예: (0.6, 0.3) → (1.0, 0.5)")
        swap_axes = st.sidebar.checkbox("🔄 X축과 Y축 바꾸기",
                                      help="길이1과 길이2의 축을 서로 바꿔서 표시합니다.")

    # 5. 태그 하이라이트 옵션 (항상 활성화)
    st.sidebar.write("### 🎨 태그 하이라이트")
    selected_tags = []

    # 태그 하이라이트 항상 활성화
    # 모든 태그 수집 (데이터가 있을 때만)
    try:
        all_tags = set()
        for _, row in landmarks_data.iterrows():
            if 'tags' in row and row['tags']:
                tags = row['tags'] if isinstance(row['tags'], list) else []
                all_tags.update(tags)

        if all_tags:
            # 태그 그룹 정의 (TagSelector.jsx 기반 + 3차 추가)
            tag_groups = {
                "1차 - 동물상": ['강아지','고양이','다람쥐','참새','사슴'],
                "1차 - 지역감": ['이국적인','동양적인'],
                "1차 - 성별감": ['남성적','중성적','여성스런'],
                "1차 - 매력": ['귀여운', '청순한', '섹시한'],
                "1차 - 연령감": ['동안의', '성숙한'],
                "1차 - 화려함": ['화려한','수수한'],
                "1차 - 온도감": ['차가운','따뜻한'],
                "1차 - 성격": ['지적인','발랄한'],
                "1차 - 인상": ['날카로운','부드러운'],
                "1차 - 얼굴형": ['시원시원한','두부상'],
                "1차 - 성향": ['고집있는','서글서글한'],
                "2차 - 분위기": ['세련된', '친근한'],
                "2차 - 품격": ['고급스러운', '생기있는'],
                "2차 - 시대감": ['현대적인','고전적인'],
                "2차 - 신뢰감": ['믿음직한','날티나는'],
                # 3차 태그 (가설 태그) 추가
                "3차 - 직업연상": ['의사상', '교사상', '예술가상', '운동선수상', '연예인상'],
            }

            # 태그 선택 방식 선택
            selection_mode = st.sidebar.radio(
                "태그 선택 방식:",
                ["📋 전체 목록", "🎯 3단계 선택"],
                help="전체 목록: 모든 태그 한 번에 보기\n3단계 선택: 1차→2차→3차로 나누어 선택"
            )

            if selection_mode == "📋 전체 목록":
                # 전체 태그 목록
                selected_tags = st.sidebar.multiselect(
                    "🎯 하이라이트할 태그들:",
                    sorted(all_tags),
                    help="선택한 태그만 색상으로 강조됩니다."
                )
            else:
                # 3단계 선택
                selected_tags = []

                # 1차 태그들 (기본 특성)
                primary_tags = []
                for group_name, group_tags in tag_groups.items():
                    if group_name.startswith("1차"):
                        available_tags = [tag for tag in group_tags if tag in all_tags]
                        primary_tags.extend(available_tags)

                if primary_tags:
                    primary_selected = st.sidebar.multiselect(
                        "🎭 1차 태그 (기본 특성):",
                        sorted(primary_tags),
                        key="primary_tags"
                    )
                    selected_tags.extend(primary_selected)

                # 2차 태그들 (세부 스타일)
                secondary_tags = []
                for group_name, group_tags in tag_groups.items():
                    if group_name.startswith("2차"):
                        available_tags = [tag for tag in group_tags if tag in all_tags]
                        secondary_tags.extend(available_tags)

                if secondary_tags:
                    secondary_selected = st.sidebar.multiselect(
                        "✨ 2차 태그 (세부 스타일):",
                        sorted(secondary_tags),
                        key="secondary_tags"
                    )
                    selected_tags.extend(secondary_selected)

                # 3차 태그들 (가설/실험) - 데이터 존재 여부 무관
                tertiary_tags = []
                for group_name, group_tags in tag_groups.items():
                    if group_name.startswith("3차"):
                        tertiary_tags.extend(group_tags)

                if tertiary_tags:
                    tertiary_selected = st.sidebar.multiselect(
                        "🔬 3차 태그 (가설/실험):",
                        sorted(tertiary_tags),
                        key="tertiary_tags"
                    )
                    selected_tags.extend(tertiary_selected)

            # 선택된 태그 수 표시
            if selected_tags:
                st.sidebar.success(f"✅ {len(selected_tags)}개 태그 선택됨")
            else:
                st.sidebar.info(f"📋 총 {len(all_tags)}개 태그 사용 가능")

    except Exception as e:
        st.sidebar.error(f"태그 데이터 로딩 오류: {e}")

    # 6. 분석 실행
    if st.sidebar.button("🚀 분석 실행"):
        execute_length_based_analysis(
            landmarks_data,
            length1_point1, length1_point2, length1_calc,
            length2_point1, length2_point2, length2_calc,
            purpose,
            normalize_ratio,
            swap_axes,
            True,  # enable_tag_highlight 항상 True
            selected_tags
        )


def load_landmarks_data():
    """데이터베이스와 JSON 파일에서 랜드마크 데이터 로드"""
    # 1. 데이터베이스에서 데이터 로드
    db_data = db_manager.get_dataframe()

    # 2. json_files 디렉토리에서 JSON 파일 로드
    json_files_path = Path("json_files")
    json_data_list = []
    if json_files_path.exists():
        for file_path in json_files_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    # 'landmarks' 데이터가 문자열이면 파싱
                    if isinstance(json_data.get('landmarks'), str):
                        json_data['landmarks'] = json.loads(json_data['landmarks'])
                    json_data_list.append(json_data)
            except Exception as e:
                st.error(f"'{file_path.name}' 파일 로딩 오류: {e}")

    json_df = pd.DataFrame(json_data_list)

    # 3. 데이터 병합
    if not json_df.empty:
        # DB 데이터와 JSON 데이터를 합치고, 'name'을 기준으로 중복 제거 (JSON 파일 우선)
        combined_data = pd.concat([db_data, json_df], ignore_index=True)
        combined_data.drop_duplicates(subset=['name'], keep='last', inplace=True)
    else:
        combined_data = db_data

    # 데이터가 비어있거나 landmarks 컬럼이 없으면 빈 DataFrame 반환
    if combined_data.empty or 'landmarks' not in combined_data.columns:
        return pd.DataFrame()

    # landmarks 컬럼이 있고 비어있지 않은 데이터만 필터링
    landmarks_data = combined_data[combined_data['landmarks'].notna()]
    
    # landmarks 데이터가 문자열 '[]'인 경우 필터링
    if not landmarks_data.empty:
        landmarks_data = landmarks_data[landmarks_data['landmarks'].apply(lambda x: x != '[]' and (isinstance(x, list) and len(x) > 0))]

    return landmarks_data



def calculate_landmarks_metric(landmarks, points, calc_type):
    """랜드마크 기반 메트릭 계산"""
    try:
        # landmarks에서 선택된 점들 추출
        selected_landmarks = []
        for point_id in points:
            landmark = next((lm for lm in landmarks if lm['mpidx'] == point_id), None)
            if landmark:
                selected_landmarks.append(landmark)

        if len(selected_landmarks) != len(points):
            return None

        # 계산 실행 - 새로운 목적 기반 구조

        # 📍 단일 점 분석
        if calc_type == "X 좌표":
            return selected_landmarks[0]['x']
        elif calc_type == "Y 좌표":
            return selected_landmarks[0]['y']
        elif calc_type == "Z 좌표":
            return selected_landmarks[0]['z']
        elif calc_type == "원점에서의 거리":
            p = selected_landmarks[0]
            return np.sqrt(p['x']**2 + p['y']**2 + p['z']**2)

        # 📏 거리 측정
        elif calc_type == "유클리드 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return np.sqrt((p1['x']-p2['x'])**2 + (p1['y']-p2['y'])**2 + (p1['z']-p2['z'])**2)
        elif calc_type == "맨하탄 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return abs(p1['x']-p2['x']) + abs(p1['y']-p2['y']) + abs(p1['z']-p2['z'])
        elif calc_type == "X축 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return abs(p1['x'] - p2['x'])
        elif calc_type == "Y축 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return abs(p1['y'] - p2['y'])
        elif calc_type == "Z축 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return abs(p1['z'] - p2['z'])

        # ⚖️ 비율 계산 (4개 점: A-B 거리 vs C-D 거리)
        elif calc_type == "거리 비율 (A-B : C-D)":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                dist1 = np.sqrt((p1['x']-p2['x'])**2 + (p1['y']-p2['y'])**2 + (p1['z']-p2['z'])**2)
                dist2 = np.sqrt((p3['x']-p4['x'])**2 + (p3['y']-p4['y'])**2 + (p3['z']-p4['z'])**2)
                return dist1 / dist2 if dist2 != 0 else 0
        elif calc_type == "X축 비율":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                dist1 = abs(p1['x'] - p2['x'])
                dist2 = abs(p3['x'] - p4['x'])
                return dist1 / dist2 if dist2 != 0 else 0
        elif calc_type == "Y축 비율":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                dist1 = abs(p1['y'] - p2['y'])
                dist2 = abs(p3['y'] - p4['y'])
                return dist1 / dist2 if dist2 != 0 else 0
        elif calc_type == "Z축 비율":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                dist1 = abs(p1['z'] - p2['z'])
                dist2 = abs(p3['z'] - p4['z'])
                return dist1 / dist2 if dist2 != 0 else 0

        # 📐 각도 측정
        elif calc_type == "벡터 각도":
            if len(selected_landmarks) >= 3:
                p1, p2, p3 = selected_landmarks[:3]
                # p2를 중심으로 p1과 p3 사이의 각도
                v1 = np.array([p1['x']-p2['x'], p1['y']-p2['y'], p1['z']-p2['z']])
                v2 = np.array([p3['x']-p2['x'], p3['y']-p2['y'], p3['z']-p2['z']])
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                cos_angle = np.clip(cos_angle, -1, 1)  # 부동소수점 오차 방지
                return np.degrees(np.arccos(cos_angle))
        elif calc_type == "평면 각도":
            if len(selected_landmarks) >= 3:
                p1, p2, p3 = selected_landmarks[:3]
                # XY 평면에서의 각도만 계산
                v1 = np.array([p1['x']-p2['x'], p1['y']-p2['y']])
                v2 = np.array([p3['x']-p2['x'], p3['y']-p2['y']])
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                cos_angle = np.clip(cos_angle, -1, 1)
                return np.degrees(np.arccos(cos_angle))
        elif calc_type == "기울기 각도":
            if len(selected_landmarks) >= 3:
                p1, p2, p3 = selected_landmarks[:3]
                # 첫 번째와 마지막 점을 연결한 직선의 기울기
                slope = (p3['y'] - p1['y']) / (p3['x'] - p1['x']) if p3['x'] != p1['x'] else float('inf')
                return np.degrees(np.arctan(slope)) if slope != float('inf') else 90

        # 📊 면적 계산
        elif calc_type == "삼각형 넓이":
            if len(selected_landmarks) >= 3:
                p1, p2, p3 = selected_landmarks[:3]
                # 3D 삼각형 넓이 계산 (외적 사용)
                v1 = np.array([p2['x']-p1['x'], p2['y']-p1['y'], p2['z']-p1['z']])
                v2 = np.array([p3['x']-p1['x'], p3['y']-p1['y'], p3['z']-p1['z']])
                cross = np.cross(v1, v2)
                return 0.5 * np.linalg.norm(cross)
        elif calc_type == "다각형 넓이":
            if len(selected_landmarks) >= 3:
                # 2D 다각형 넓이 (Shoelace formula)
                points = [(p['x'], p['y']) for p in selected_landmarks]
                n = len(points)
                area = 0
                for i in range(n):
                    j = (i + 1) % n
                    area += points[i][0] * points[j][1]
                    area -= points[j][0] * points[i][1]
                return abs(area) / 2

        # ⚖️ 대칭성 분석
        elif calc_type == "좌우 대칭 비율":
            if len(selected_landmarks) >= 4:
                # 첫 두 점 vs 나중 두 점의 거리 비교
                p1, p2, p3, p4 = selected_landmarks[:4]
                left_dist = np.sqrt((p1['x']-p2['x'])**2 + (p1['y']-p2['y'])**2)
                right_dist = np.sqrt((p3['x']-p4['x'])**2 + (p3['y']-p4['y'])**2)
                return left_dist / right_dist if right_dist != 0 else 0
        elif calc_type == "중심축 기준 거리차":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                # 중심축을 Y축으로 가정하고 좌우 점들의 중심축으로부터의 거리 차이
                center_x = (p1['x'] + p2['x'] + p3['x'] + p4['x']) / 4
                left_dist = abs(p1['x'] - center_x) + abs(p2['x'] - center_x)
                right_dist = abs(p3['x'] - center_x) + abs(p4['x'] - center_x)
                return abs(left_dist - right_dist)
        elif calc_type == "대칭도 점수":
            if len(selected_landmarks) >= 4:
                # 0에 가까울수록 대칭적
                p1, p2, p3, p4 = selected_landmarks[:4]
                center_x = (p1['x'] + p2['x'] + p3['x'] + p4['x']) / 4
                left_deviation = np.sqrt((p1['x'] - center_x)**2 + (p2['x'] - center_x)**2)
                right_deviation = np.sqrt((p3['x'] - center_x)**2 + (p4['x'] - center_x)**2)
                return abs(left_deviation - right_deviation)

        return None

    except Exception as e:
        st.error(f"계산 오류: {e}")
        return None


def execute_length_based_analysis(landmarks_data, l1_p1, l1_p2, l1_calc, l2_p1, l2_p2, l2_calc, purpose, normalize_ratio=False, swap_axes=False, enable_tag_highlight=False, selected_tags=None):
    """길이 기반 분석 실행"""
    if selected_tags is None:
        selected_tags = []
    st.write("### 🔄 분석 실행 중...")

    # 각 데이터에 대해 길이1, 길이2 계산
    length1_values = []
    length2_values = []
    names = []
    tags_list = []
    colors = []

    # 태그별 컬러 매핑 생성
    if enable_tag_highlight:
        all_tags = set()
        for _, row in landmarks_data.iterrows():
            if 'tags' in row and row['tags']:
                tags = row['tags'] if isinstance(row['tags'], list) else []
                all_tags.update(tags)

        # 태그별 고유 색상 생성
        color_palette = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel + px.colors.qualitative.Set1
        tag_color_map = {tag: color_palette[i % len(color_palette)] for i, tag in enumerate(sorted(all_tags))}
        tag_color_map['기타'] = '#808080'  # 회색

    for _, row in landmarks_data.iterrows():
        try:
            # 랜드마크 데이터 파싱
            if isinstance(row['landmarks'], str):
                landmarks = json.loads(row['landmarks'])
            else:
                landmarks = row['landmarks']

            # 길이1 계산
            length1 = calculate_length(landmarks, l1_p1, l1_p2, l1_calc)
            # 길이2 계산
            length2 = calculate_length(landmarks, l2_p1, l2_p2, l2_calc)

            if length1 is not None and length2 is not None:
                final_length1 = length1
                final_length2 = length2

                # 정규화 적용 (비율 계산이고 normalize_ratio가 True일 때)
                if purpose == "⚖️ 비율 계산" and normalize_ratio and final_length1 != 0:
                    # X축(길이1)을 1로 고정하고 Y축(길이2)을 비례적으로 스케일링
                    scale_factor = final_length1
                    final_length1 = 1.0
                    final_length2 = final_length2 / scale_factor if scale_factor != 0 else 0


                # 소수점 둘째자리까지 반올림
                final_length1 = round(final_length1, 2)
                final_length2 = round(final_length2, 2)

                # 태그 정보 수집
                row_tags = []
                if 'tags' in row and row['tags']:
                    row_tags = row['tags'] if isinstance(row['tags'], list) else []

                # 색상 결정
                if enable_tag_highlight and selected_tags:
                    # 특정 태그들이 선택된 경우에만 색상 적용
                    matching_tags = [tag for tag in selected_tags if tag in row_tags]
                    if matching_tags:
                        # 선택된 태그 중 첫 번째 매칭되는 태그의 색상 사용
                        color = tag_color_map.get(matching_tags[0], '#FF0000')
                        opacity = 1.0
                    else:
                        color = '#808080'  # 회색으로 dimmed
                        opacity = 0.6
                else:
                    # 기본 회색 (태그 하이라이트 비활성화 또는 태그 미선택 시)
                    color = '#808080'  # 회색
                    opacity = 1.0

                length1_values.append(final_length1)
                length2_values.append(final_length2)
                names.append(row['name'])
                tags_list.append(', '.join(row_tags) if row_tags else '태그없음')
                colors.append(color)

        except Exception as e:
            st.error(f"데이터 처리 오류 ({row['name']}): {e}")
            continue

    if not length1_values:
        st.error("❌ 계산할 수 있는 데이터가 없습니다.")
        return

    # 결과 표시
    st.write("### 📊 분석 결과")

    # 결과 데이터프레임 생성
    result_df = pd.DataFrame({
        'name': names,
        'length1': length1_values,
        'length2': length2_values,
        'tags': tags_list,
        'color': colors
    })

    # 모든 경우에 산점도로 표시
    col1, col2 = st.columns([2, 1])

    with col1:

        if purpose == "⚖️ 비율 계산":
            # 비율 계산인 경우: X축 - 길이1, Y축 - 길이2의 산점도

            # 축 바꾸기 적용
            if swap_axes:
                x_data, y_data = 'length2', 'length1'
                if normalize_ratio:
                    title = f'정규화된 비율 (Y : 1)'
                    x_label = f'길이2 (정규화 비율)'
                    y_label = f'길이1 (정규화됨)'
                else:
                    title = f'길이2 vs 길이1'
                    x_label = f'길이2 ({l2_calc})'
                    y_label = f'길이1 ({l1_calc})'
            else:
                x_data, y_data = 'length1', 'length2'
                if normalize_ratio:
                    title = f'정규화된 비율 (1 : Y)'
                    x_label = f'길이1 (정규화됨)'
                    y_label = f'길이2 (정규화 비율)'
                else:
                    title = f'길이1 vs 길이2'
                    x_label = f'길이1 ({l1_calc})'
                    y_label = f'길이2 ({l2_calc})'

            # 태그 하이라이트가 활성화되어 있으면 색상 적용
            if enable_tag_highlight:
                fig = go.Figure()

                # 각 점을 개별적으로 추가하여 색상 제어
                for idx, row in result_df.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[row[x_data]],
                        y=[row[y_data]],
                        mode='markers',
                        marker=dict(
                            color=row['color'],
                            size=8,
                            opacity=0.8,
                            line=dict(width=1, color='white')
                        ),
                        hovertemplate=f"이름: {row['name']}<br>태그: {row['tags']}<br>길이1: {row['length1']}<br>길이2: {row['length2']}<extra></extra>",
                        showlegend=False,
                        name=row['name']
                    ))

                fig.update_layout(
                    title=title,
                    xaxis_title=x_label,
                    yaxis_title=y_label
                )
            else:
                fig = px.scatter(
                    result_df,
                    x=x_data,
                    y=y_data,
                    title=title,
                    labels={x_data: x_label, y_data: y_label},
                    hover_data=['name', 'tags']
                )
        else:
            # 거리 측정인 경우: 히스토그램 대신 strip plot(산점도)로 변경하여 hover 지원
            # Y축에 약간의 랜덤 지터 추가하여 점들이 겹치지 않게 함
            np.random.seed(42)  # 일관된 결과를 위해
            result_df['y_jitter'] = np.random.uniform(-0.1, 0.1, len(result_df))

            if enable_tag_highlight:
                fig = go.Figure()

                # 각 점을 개별적으로 추가하여 색상 제어
                for idx, row in result_df.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[row['length1']],
                        y=[row['y_jitter']],
                        mode='markers',
                        marker=dict(
                            color=row['color'],
                            size=8,
                            opacity=0.8,
                            line=dict(width=1, color='white')
                        ),
                        hovertemplate=f"이름: {row['name']}<br>태그: {row['tags']}<br>길이1: {row['length1']}<br>길이2: {row['length2']}<extra></extra>",
                        showlegend=False,
                        name=row['name']
                    ))

                fig.update_layout(
                    title=f'거리 분포 ({l1_calc}) - 태그별 색상 구분',
                    xaxis_title=f'거리 ({l1_calc})',
                    yaxis_title=""
                )
                # Y축 숨기기 (의미없는 축이므로)
                fig.update_yaxes(showticklabels=False)
            else:
                fig = px.scatter(
                    result_df,
                    x='length1',
                    y='y_jitter',
                    title=f'거리 분포 ({l1_calc}) - 각 점이 개별 데이터',
                    labels={'length1': f'거리 ({l1_calc})', 'y_jitter': '분산 (시각화용)'},
                    hover_data=['name', 'tags']
                )
                # Y축 숨기기 (의미없는 축이므로)
                fig.update_yaxes(showticklabels=False, title_text="")

        st.plotly_chart(fig, use_container_width=True)

        # 태그 하이라이트가 활성화되어 있으면 태그 범례 표시
        if enable_tag_highlight:
            st.write("#### 🏷️ 태그 범례")

            # 현재 데이터의 태그별 개수 계산
            tag_counts = {}
            for tags_str in tags_list:
                if tags_str != '태그없음':
                    for tag in tags_str.split(', '):
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                else:
                    tag_counts['태그없음'] = tag_counts.get('태그없음', 0) + 1

            # 태그별 색상 박스와 개수 표시
            cols = st.columns(min(4, len(tag_counts)))
            for i, (tag, count) in enumerate(sorted(tag_counts.items())):
                with cols[i % len(cols)]:
                    if enable_tag_highlight:
                        color = tag_color_map.get(tag, '#808080')
                        # HTML을 사용해 색상 박스 표시
                        st.markdown(
                            f'<div style="display: flex; align-items: center;">'
                            f'<div style="width: 20px; height: 20px; background-color: {color}; '
                            f'border: 1px solid #ccc; margin-right: 8px; border-radius: 3px;"></div>'
                            f'<span><strong>{tag}</strong> ({count}개)</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            # 필터링 정보 표시
            if selected_tags:
                st.info(f"🎯 선택된 태그: {', '.join(selected_tags)} (선택된 태그만 색상으로 표시)")
            else:
                st.info("💡 모든 점이 회색으로 표시됩니다. 특정 태그를 색상으로 하이라이트하려면 위에서 선택하세요.")



    with col2:
        if purpose == "📏 거리 측정":
            st.write("#### 📈 거리 통계")
            st.write(f"**평균:** {np.mean(length1_values):.2f}")
            st.write(f"**표준편차:** {np.std(length1_values):.2f}")
            st.write(f"**최소값:** {np.min(length1_values):.2f}")
            st.write(f"**최대값:** {np.max(length1_values):.2f}")
            st.write(f"**유니크 값:** {len(set(length1_values))}개")
        else:
            st.write("#### 📈 길이1 통계")
            st.write(f"**평균:** {np.mean(length1_values):.2f}")
            st.write(f"**표준편차:** {np.std(length1_values):.2f}")

            st.write("#### 📈 길이2 통계")
            st.write(f"**평균:** {np.mean(length2_values):.2f}")
            st.write(f"**표준편차:** {np.std(length2_values):.2f}")

    # 상세 데이터 테이블
    with st.expander("📋 상세 데이터 보기"):
        # 색상 컬럼 제거 후 표시
        display_df = result_df.drop('color', axis=1) if 'color' in result_df.columns else result_df
        st.dataframe(display_df, use_container_width=True)

        # 태그별 통계
        if enable_tag_highlight and tags_list:
            st.write("##### 📊 태그별 통계")
            tag_stats = {}
            for i, tags_str in enumerate(tags_list):
                if tags_str != '태그없음':
                    primary_tag = tags_str.split(', ')[0]
                    if primary_tag not in tag_stats:
                        tag_stats[primary_tag] = {'count': 0, 'values': []}
                    tag_stats[primary_tag]['count'] += 1
                    tag_stats[primary_tag]['values'].append(length1_values[i])

            if tag_stats:
                stats_data = []
                for tag, data in tag_stats.items():
                    stats_data.append({
                        '태그': tag,
                        '개수': data['count'],
                        '평균': f"{np.mean(data['values']):.2f}",
                        '표준편차': f"{np.std(data['values']):.2f}",
                        '최소값': f"{np.min(data['values']):.2f}",
                        '최대값': f"{np.max(data['values']):.2f}"
                    })
                st.dataframe(pd.DataFrame(stats_data), use_container_width=True)


def calculate_length(landmarks, point1_id, point2_id, calc_type):
    """두 점 사이의 거리 계산"""
    try:
        # 점 찾기
        p1 = next((lm for lm in landmarks if lm['mpidx'] == point1_id), None)
        p2 = next((lm for lm in landmarks if lm['mpidx'] == point2_id), None)

        if not p1 or not p2:
            return None

        if calc_type == "직선거리":
            return np.sqrt((p1['x']-p2['x'])**2 + (p1['y']-p2['y'])**2 + (p1['z']-p2['z'])**2)
        elif calc_type == "X좌표거리":
            return abs(p1['x'] - p2['x'])
        elif calc_type == "Y좌표거리":
            return abs(p1['y'] - p2['y'])
        else:
            return None

    except Exception as e:
        return None


# def execute_landmarks_analysis(data, points, calc_type, analysis_tool):
#     """랜드마크 분석 실행 - 고급 분석 기능 (현재 미사용)"""
#     st.write("### 🔄 분석 실행 중...")
#
#     # 각 데이터에 대해 메트릭 계산
#     calculated_values = []
#     names = []
#
#     for _, row in data.iterrows():
#         value = calculate_landmarks_metric(row['landmarks'], points, calc_type)
#         if value is not None:
#             calculated_values.append(value)
#             names.append(row['name'])
#
#     if not calculated_values:
#         st.error("❌ 계산된 값이 없습니다. 점 선택이나 계산 방식을 확인해주세요.")
#         return
#
#     # 결과 DataFrame 생성
#     result_df = pd.DataFrame({
#         'name': names,
#         'value': calculated_values
#     })
#
#     # 분석 결과 표시
#     st.write("### 📊 분석 결과")
#
#     col1, col2 = st.columns([2, 1])
#
#     with col1:
#         # 시각화
#         if analysis_tool == "히스토그램":
#             fig = px.histogram(
#                 result_df,
#                 x='value',
#                 title=f'{calc_type} 분포 (점: {points})',
#                 labels={'value': calc_type, 'count': '빈도'}
#             )
#             st.plotly_chart(fig, use_container_width=True)
#
#         elif analysis_tool == "박스플롯":
#             fig = px.box(
#                 result_df,
#                 y='value',
#                 title=f'{calc_type} 박스플롯 (점: {points})',
#                 labels={'value': calc_type}
#             )
#             st.plotly_chart(fig, use_container_width=True)
#
#     with col2:
#         # 통계 정보
#         st.write("#### 📈 통계 정보")
#         st.write(f"**평균:** {np.mean(calculated_values):.4f}")
#         st.write(f"**중앙값:** {np.median(calculated_values):.4f}")
#         st.write(f"**표준편차:** {np.std(calculated_values):.4f}")
#         st.write(f"**최솟값:** {np.min(calculated_values):.4f}")
#         st.write(f"**최댓값:** {np.max(calculated_values):.4f}")
#         st.write(f"**데이터 수:** {len(calculated_values)}")
#
#         # 계산 정보
#         st.write("#### ⚙️ 계산 정보")
#         st.write(f"**선택 점:** {points}")
#         st.write(f"**계산 방식:** {calc_type}")
#
#     # 상세 데이터 테이블
#     with st.expander("📋 상세 데이터 보기"):
#         st.dataframe(result_df, use_container_width=True)




if __name__ == "__main__":
    main()
