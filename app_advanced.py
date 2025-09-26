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
from collections import Counter
from itertools import combinations

# Database and engines
from database.db_manager import db_manager

# Page config
st.set_page_config(
    page_title="Face Coordinate Analyzer",
    page_icon="🎭",
    layout="wide"
)

def get_tag_groups():
    """태그 그룹 정보를 반환합니다."""
    return {
        "추상 - 분위기": ['세련된', '친근한'],
        "추상 - 품격": ['고급스러운', '생기있는'],
        "추상 - 시대감": ['현대적인','고전적인'],
        "추상 - 신뢰감": ['믿음직한','날티나는'],
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
        "2차 - 이마": ['forehead-높이-긴', 'forehead-높이-보통', 'forehead-높이-짧은', 'forehead-너비-넓은', 'forehead-너비-보통', 'forehead-너비-좁은'],
        "2차 - 눈썹": ['eyebrow-눈과의거리-먼', 'eyebrow-눈과의거리-보통', 'eyebrow-눈과의거리-가까운', 'eyebrow-형태-공격', 'eyebrow-형태-아치', 'eyebrow-형태-물결', 'eyebrow-형태-일자', 'eyebrow-형태-둥근', 'eyebrow-형태-처진', 'eyebrow-곡률-큰', 'eyebrow-곡률-보통', 'eyebrow-곡률-작은', 'eyebrow-거리-먼', 'eyebrow-거리-보통', 'eyebrow-거리-가까운', 'eyebrow-길이-긴', 'eyebrow-길이-보통', 'eyebrow-길이-짧은', 'eyebrow-두께-두꺼운', 'eyebrow-두께-보통', 'eyebrow-두께-얇은', 'eyebrow-숱-진한', 'eyebrow-숱-보통', 'eyebrow-숱-흐린'],
        "2차 - 눈": ['eye-인상-사나운', 'eye-인상-똘망똘망한', 'eye-인상-보통', 'eye-인상-순한', 'eye-인상-졸린', 'eye-미간-먼', 'eye-미간-보통', 'eye-미간-좁은', 'eye-모양-시원한', 'eye-모양-찢어진', 'eye-모양-보통', 'eye-모양-동그란', 'eye-모양-답답한', 'eye-크기-큰', 'eye-크기-보통', 'eye-크기-작은', 'eye-길이-긴', 'eye-길이-보통', 'eye-길이-짧은', 'eye-높이-높은', 'eye-높이-보통', 'eye-높이-낮은', 'eye-쌍꺼풀-없음', 'eye-쌍꺼풀-아웃', 'eye-쌍꺼풀-세미아웃', 'eye-쌍꺼풀-인아웃', 'eye-쌍꺼풀-인', 'eye-애교-많은', 'eye-애교-보통', 'eye-애교-적은', 'eye-눈밑지-심한', 'eye-눈밑지-약간', 'eye-눈밑지-없음', 'eye-동공-사백안', 'eye-동공-보통', 'eye-동공-삼백안', 'eye-동공-반가려짐'],
        "2차 - 코": ['nose-모양-화살코', 'nose-모양-보통', 'nose-모양-복코', 'nose-모양-들창코', 'nose-길이-긴', 'nose-길이-보통', 'nose-길이-짧은', 'nose-콧대-두꺼운', 'nose-콧대-보통', 'nose-콧대-얇은', 'nose-콧볼-넓은', 'nose-콧볼-보통', 'nose-콧볼-좁은', 'nose-코끝-넓은', 'nose-코끝-보통', 'nose-코끝-좁은', 'nose-콧구멍-넓은', 'nose-콧구멍-보통', 'nose-콧구멍-긴', 'nose-콧구멍-좁은'],
        "2차 - 입": ['mouth-너비-넓은', 'mouth-너비-보통', 'mouth-너비-좁은', 'mouth-두께-두꺼운', 'mouth-두께-보통', 'mouth-두께-얇은', 'mouth-입꼬리-올라간', 'mouth-입꼬리-평평한', 'mouth-입꼬리-내려간', 'mouth-위두께-두꺼운', 'mouth-위두께-보통', 'mouth-위두께-얇은', 'mouth-아래두께-두꺼운', 'mouth-아래두께-보통', 'mouth-아래두께-얇은', 'mouth-전체입술선-또렷', 'mouth-전체입술선-보통', 'mouth-전체입술선-흐릿', 'mouth-큐피드-또렷', 'mouth-큐피드-둥글', 'mouth-큐피드-1자', 'mouth-입술결절-뾰족', 'mouth-입술결절-1자', 'mouth-입술결절-함몰', 'mouth-위긴장도-있음', 'mouth-위긴장도-보통', 'mouth-위긴장도-없음', 'mouth-아래긴장도-있음', 'mouth-아래긴장도-보통', 'mouth-아래긴장도-없음', 'mouth-인중길이-짧아', 'mouth-인중길이-보통', 'mouth-인중길이-길어', 'mouth-인중너비-넓어', 'mouth-인중너비-보통', 'mouth-인중너비-좁아', 'mouth-팔자-깊은', 'mouth-팔자-보통', 'mouth-팔자-없음'],
        "2차 - 직업연상": ['의사상', '교사상', '예술가상', '운동선수상', '연예인상'],
        "2차 - 윤곽": ['silhouette-얼굴형-달걀형', 'silhouette-얼굴형-역삼각형', 'silhouette-얼굴형-긴', 'silhouette-얼굴형-동글', 'silhouette-얼굴형-사각형', 'silhouette-옆광대-크기-큰', 'silhouette-옆광대-크기-보통', 'silhouette-옆광대-크기-작은', 'silhouette-옆광대-높이-높은', 'silhouette-옆광대-높이-보통', 'silhouette-옆광대-높이-낮은', 'silhouette-옆광대-위치-밖', 'silhouette-옆광대-위치-보통', 'silhouette-옆광대-위치-안', 'silhouette-앞광대-크기-큰', 'silhouette-앞광대-크기-보통', 'silhouette-앞광대-크기-작은', 'silhouette-앞광대-높이-높은', 'silhouette-앞광대-높이-보통', 'silhouette-앞광대-높이-낮은', 'silhouette-턱-발달-발달', 'silhouette-턱-발달-보통', 'silhouette-턱-발달-무턱', 'silhouette-턱-형태-뾰족한', 'silhouette-턱-형태-보통', 'silhouette-턱-형태-각진', 'silhouette-턱-길이-긴', 'silhouette-턱-길이-보통', 'silhouette-턱-길이-짧은', 'silhouette-볼-살-살X', 'silhouette-볼-살-보통', 'silhouette-볼-살-살O', 'silhouette-볼-탄력-쳐진', 'silhouette-볼-탄력-보통', 'silhouette-볼-탄력-탄력'],
    }

def main():
    st.title("🎭 Face Coordinate Analyzer")
    st.markdown("**실시간 좌표 계산 기반 얼굴 분석 플랫폼**")

    # 사이드바에 데이터베이스 관리 기능 추가
    render_database_management_sidebar()

    # 랜드마크 데이터 로드
    landmarks_data = load_landmarks_data()

    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["🧮 좌표 분석", "🔗 태그 연관성 분석", "🌊 태그 관계도"])

    with tab1:
        render_landmarks_analysis_tab(landmarks_data)

    with tab2:
        render_tag_analysis_tab(landmarks_data)

    with tab3:
        render_sankey_diagram_tab(landmarks_data)

def render_landmarks_analysis_tab(landmarks_data):
    """좌표 분석 탭 렌더링"""
    st.header("🧮 좌표 분석 (실시간 계산)")
    st.markdown("두 거리를 기반으로 한 비교 분석")

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
            tag_groups = get_tag_groups()

            # 태그 선택 방식 선택
            selection_mode = st.sidebar.radio(
                "태그 선택 방식:",
                ["🎯 3단계 선택", "📋 전체 목록"],
                help="3단계 선택: 1차→2차→3차로 나누어 선택\n전체 목록: 모든 태그 한 번에 보기"
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

                # 추상 태그들 (전체적인 느낌)
                abstract_tags = []
                for group_name, group_tags in tag_groups.items():
                    if group_name.startswith("추상"):
                        available_tags = [tag for tag in group_tags if tag in all_tags]
                        abstract_tags.extend(available_tags)

                if abstract_tags:
                    abstract_selected = st.sidebar.multiselect(
                        "🌟 추상 태그 (전체적인 느낌):",
                        sorted(abstract_tags),
                        key="abstract_tags"
                    )
                    selected_tags.extend(abstract_selected)

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

                # 2차 태그들 (부위별 세부사항)
                secondary_tags = []
                for group_name, group_tags in tag_groups.items():
                    if group_name.startswith("2차"):
                        secondary_tags.extend(group_tags)

                if secondary_tags:
                    secondary_selected = st.sidebar.multiselect(
                        "🔬 2차 태그 (부위별 세부사항):",
                        sorted(secondary_tags),
                        key="secondary_tags"
                    )
                    selected_tags.extend(secondary_selected)

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

def render_tag_analysis_tab(landmarks_data):
    """태그 연관성 분석 탭 렌더링"""
    st.header("🔗 태그 연관성 분석")
    st.markdown("데이터에 포함된 태그들의 동시 출현 빈도를 분석합니다.")

    if landmarks_data.empty or 'tags' not in landmarks_data.columns:
        st.warning("태그 데이터가 포함된 파일이 필요합니다.")
        return

    tag_lists = landmarks_data['tags'].dropna().tolist()

    # 모든 고유 태그 추출 (데이터 + 정의된 태그 그룹)
    data_tags = set(tag for sublist in tag_lists for tag in sublist if isinstance(sublist, list))

    # get_tag_groups()에서 정의된 모든 태그 추가
    tag_groups = get_tag_groups()
    defined_tags = set()
    for tags in tag_groups.values():
        defined_tags.update(tags)

    # 데이터의 태그와 정의된 태그 합치기
    all_unique_tags = sorted(list(data_tags.union(defined_tags)))

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📊 분석 설정")
        itemset_size = st.number_input("분석할 태그 조합 개수", min_value=2, max_value=5, value=2)
        top_n = st.slider("상위 몇 개를 보시겠습니까?", min_value=5, max_value=50, value=20)

    with col2:
        st.subheader("🔍 태그 필터")

        # 태그 선택 방식 선택
        filter_selection_mode = st.radio(
            "태그 선택 방식:",
            ["🎯 3단계 선택", "📋 전체 목록"],
            key="filter_selection_mode"
        )

        filter_tags = []

        if filter_selection_mode == "📋 전체 목록":
            filter_tags = st.multiselect(
                "특정 태그가 모두 포함된 데이터만 분석:",
                options=all_unique_tags,
                help="선택한 모든 태그가 포함된 데이터만으로 분석합니다 (AND 조건)"
            )
        else:
            # 3단계 선택
            # 추상 태그들
            abstract_tags = []
            for category, tags in tag_groups.items():
                if '추상' in category:
                    abstract_tags.extend(tags)

            if abstract_tags:
                abstract_selected = st.multiselect(
                    "🌟 추상 태그:",
                    sorted(abstract_tags),
                    key="filter_abstract"
                )
                filter_tags.extend(abstract_selected)

            # 1차 태그들
            primary_tags = []
            for category, tags in tag_groups.items():
                if '1차' in category:
                    primary_tags.extend(tags)

            if primary_tags:
                primary_selected = st.multiselect(
                    "🥇 1차 태그:",
                    sorted(primary_tags),
                    key="filter_primary"
                )
                filter_tags.extend(primary_selected)

            # 2차 태그들
            secondary_tags = []
            for category, tags in tag_groups.items():
                if '2차' in category:
                    secondary_tags.extend(tags)

            if secondary_tags:
                secondary_selected = st.multiselect(
                    "🥈 2차 태그:",
                    sorted(secondary_tags),
                    key="filter_secondary"
                )
                filter_tags.extend(secondary_selected)

    # 태그 그룹 정보 및 역방향 매핑 생성
    tag_groups = get_tag_groups()
    tag_to_category = {}
    for category, tags in tag_groups.items():
        cat_level = category.split(' ')[0]
        for tag in tags:
            tag_to_category[tag] = cat_level

    def format_combination_label(combination):
        parts = {'추상': [], '1차': [], '2차': []}
        for tag in combination:
            category_level = tag_to_category.get(tag, '기타').split('-')[0]
            if '추상' in category_level:
                parts['추상'].append(tag)
            elif '1차' in category_level:
                parts['1차'].append(tag)
            elif '2차' in category_level:
                parts['2차'].append(tag)
        
        label_parts = []
        for level in ['추상', '1차', '2차']:
            if parts[level]:
                label_parts.append(', '.join(parts[level]))
            else:
                label_parts.append('..')
        return ' / '.join(label_parts)

    # 태그 필터링 적용
    if filter_tags:
        # 선택된 태그가 모두 포함된 데이터만 필터링
        filtered_tag_lists = []
        for tags in tag_lists:
            if isinstance(tags, list) and all(filter_tag in tags for filter_tag in filter_tags):
                filtered_tag_lists.append(tags)
        tag_lists = filtered_tag_lists

        if not tag_lists:
            st.warning(f"선택된 모든 태그({', '.join(filter_tags)})가 포함된 데이터가 없습니다.")
            return

    # 조합 계산
    all_combinations = []
    for tags in tag_lists:
        if isinstance(tags, list) and len(tags) >= itemset_size:
            combinations_from_tags = list(combinations(sorted(tags), itemset_size))

            # 필터 태그가 선택된 경우, 조합에도 모든 필터 태그가 포함된 것만 추가
            if filter_tags:
                for combo in combinations_from_tags:
                    if all(filter_tag in combo for filter_tag in filter_tags):
                        all_combinations.append(combo)
            else:
                all_combinations.extend(combinations_from_tags)

    if not all_combinations:
        st.warning(f"{itemset_size}개 이상의 태그를 가진 데이터가 없습니다.")
        return

    combination_counts = Counter(all_combinations)
    most_common_combinations = combination_counts.most_common(top_n)

    # 조합별 파일 리스트 생성
    combination_files = {}
    for tags in tag_lists:
        if isinstance(tags, list) and len(tags) >= itemset_size:
            combinations_from_tags = list(combinations(sorted(tags), itemset_size))

            # 해당 태그 리스트가 어떤 파일인지 찾기
            file_name = None
            for idx, row_tags in enumerate(landmarks_data['tags'].dropna().tolist()):
                if isinstance(row_tags, list) and row_tags == tags:
                    file_name = landmarks_data.iloc[idx]['name'] if 'name' in landmarks_data.columns else f"파일_{idx+1}"
                    break

            for combo in combinations_from_tags:
                if filter_tags and not all(filter_tag in combo for filter_tag in filter_tags):
                    continue
                if combo not in combination_files:
                    combination_files[combo] = []
                if file_name:
                    combination_files[combo].append(file_name)

    # 막대 그래프 시각화
    filter_info = f" (필터: {', '.join(filter_tags)})" if filter_tags else ""
    st.subheader(f"가장 자주 함께 사용된 태그 조합 (상위 {top_n}개){filter_info}")
    if most_common_combinations:
        comb_df = pd.DataFrame(most_common_combinations, columns=['combination', 'count'])
        comb_df['combination_str'] = comb_df['combination'].apply(format_combination_label)

        # 파일 리스트 추가
        comb_df['files'] = comb_df['combination'].apply(lambda combo:
            ', '.join(combination_files.get(combo, [])[:5]) +
            (f' 외 {len(combination_files.get(combo, []))-5}개' if len(combination_files.get(combo, [])) > 5 else '')
        )

        fig = px.bar(
            comb_df,
            x='count',
            y='combination_str',
            orientation='h',
            title=f'{itemset_size}개 태그 조합의 동시 출현 빈도',
            labels={'count': '빈도', 'combination_str': '태그 조합'},
            hover_data={'files': True}
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})

        # 호버 템플릿 커스터마이징
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>" +
                         "빈도: %{x}<br>" +
                         "파일: %{customdata[0]}<br>" +
                         "<extra></extra>",
            customdata=comb_df[['files']].values
        )

        st.plotly_chart(fig, use_container_width=True)

        # 각 태그 조합별 구성 파일 상세 표시
        st.subheader("📋 각 조합별 구성 파일 목록")
        for combo, count in most_common_combinations:
            combo_label = format_combination_label(combo)
            files = combination_files.get(combo, [])

            with st.expander(f"**{combo_label}** ({count}개 파일)", expanded=False):
                if files:
                    # 파일 리스트를 데이터프레임으로 표시
                    files_df = pd.DataFrame({'파일명': files})
                    files_df.index = files_df.index + 1  # 1부터 시작하는 인덱스
                    st.dataframe(files_df, use_container_width=True)
                else:
                    st.info("해당 조합의 파일이 없습니다.")
    else:
        st.info("표시할 데이터가 없습니다.")

    # 히트맵 시각화 (2개 조합일 때만)
    if itemset_size == 2:
        st.subheader(f"태그 동시 출현 빈도 히트맵{filter_info}")

        all_unique_tags_heatmap = sorted(list(set(tag for sublist in tag_lists for tag in sublist)))
        
        heatmap_df = pd.DataFrame(0, index=all_unique_tags_heatmap, columns=all_unique_tags_heatmap)

        for combo, count in combination_counts.items():
            tag1, tag2 = combo
            heatmap_df.loc[tag1, tag2] = count
            heatmap_df.loc[tag2, tag1] = count
        
        np.fill_diagonal(heatmap_df.values, 0)

        if not heatmap_df.empty:
            fig_heatmap = px.imshow(
                heatmap_df,
                title="태그 동시 출현 빈도 히트맵",
                labels=dict(x="태그", y="태그", color="빈도"),
                color_continuous_scale="Blues"
            )
            fig_heatmap.update_xaxes(side="bottom")
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("히트맵을 생성할 데이터가 없습니다.")

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



def render_sankey_diagram_tab(landmarks_data):
    """태그 관계도 (Sankey Diagram) 탭 렌더링"""
    st.header("🌊 태그 관계도 (Sankey Diagram)")
    st.markdown("추상 → 1차 → 2차 태그 간의 관계와 빈도를 시각화합니다.")

    if landmarks_data.empty or 'tags' not in landmarks_data.columns:
        st.warning("태그 데이터가 포함된 파일이 필요합니다.")
        return

    # 태그 관계 분석
    tag_relationships = analyze_tag_relationships(landmarks_data)

    if not tag_relationships:
        st.info("태그 관계를 분석할 수 있는 데이터가 충분하지 않습니다.")
        return

    # 메인 페이지에 필터 옵션 추가
    st.write("### 🎯 관계도 필터")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # 관계 타입 선택
        relationship_type = st.selectbox(
            "관계 타입:",
            ["전체 흐름 (추상→1차→2차)", "추상→1차만", "1차→2차만"],
            help="보고 싶은 관계 타입을 선택하세요."
        )

    with col2:
        # 태그 선택 (관계 타입에 따라)
        if "추상" in relationship_type:
            # 추상 태그 선택
            available_abstract_tags = sorted(tag_relationships['abstract_tags'])
            selected_abstract_tag = st.selectbox(
                "추상 태그:",
                ["전체"] + available_abstract_tags,
                help="특정 추상 태그 선택"
            )
            selected_primary_tag = "전체"
        elif relationship_type == "1차→2차만":
            # 1차 태그 선택
            available_primary_tags = sorted(tag_relationships['primary_tags'])
            selected_primary_tag = st.selectbox(
                "1차 태그:",
                ["전체"] + available_primary_tags,
                help="특정 1차 태그 선택"
            )
            selected_abstract_tag = "전체"
        else:
            selected_abstract_tag = "전체"
            selected_primary_tag = "전체"
            st.empty()  # 빈 공간

    with col3:
        # 최소 빈도 설정
        min_frequency = st.slider(
            "최소 빈도:",
            min_value=1,
            max_value=10,
            value=2,
            help="이 빈도 이상의 관계만 표시됩니다."
        )

    # Sankey 다이어그램 생성
    create_sankey_diagram(tag_relationships, selected_abstract_tag, min_frequency, relationship_type, selected_primary_tag)

def analyze_tag_relationships(landmarks_data):
    """태그 간 관계 분석"""
    tag_groups = get_tag_groups()

    # 태그 레벨별 분류
    abstract_tags = set()
    primary_tags = set()
    secondary_tags = set()

    for group_name, tags in tag_groups.items():
        if group_name.startswith("추상"):
            abstract_tags.update(tags)
        elif group_name.startswith("1차"):
            primary_tags.update(tags)
        elif group_name.startswith("2차"):
            secondary_tags.update(tags)

    # 관계 분석
    abstract_to_primary = {}
    primary_to_secondary = {}
    abstract_to_secondary = {}

    for _, row in landmarks_data.iterrows():
        if 'tags' in row and row['tags']:
            row_tags = row['tags'] if isinstance(row['tags'], list) else []

            # 해당 행의 태그들을 레벨별로 분류
            row_abstract = [tag for tag in row_tags if tag in abstract_tags]
            row_primary = [tag for tag in row_tags if tag in primary_tags]
            row_secondary = [tag for tag in row_tags if tag in secondary_tags]

            # 추상 → 1차 관계
            for abs_tag in row_abstract:
                for prim_tag in row_primary:
                    key = (abs_tag, prim_tag)
                    abstract_to_primary[key] = abstract_to_primary.get(key, 0) + 1

            # 1차 → 2차 관계
            for prim_tag in row_primary:
                for sec_tag in row_secondary:
                    key = (prim_tag, sec_tag)
                    primary_to_secondary[key] = primary_to_secondary.get(key, 0) + 1

            # 추상 → 2차 관계 (직접 연결)
            for abs_tag in row_abstract:
                for sec_tag in row_secondary:
                    key = (abs_tag, sec_tag)
                    abstract_to_secondary[key] = abstract_to_secondary.get(key, 0) + 1

    return {
        'abstract_to_primary': abstract_to_primary,
        'primary_to_secondary': primary_to_secondary,
        'abstract_to_secondary': abstract_to_secondary,
        'abstract_tags': list(abstract_tags),
        'primary_tags': list(primary_tags),
        'secondary_tags': list(secondary_tags)
    }

def create_sankey_diagram(relationships, selected_abstract_tag="전체", min_frequency=2, relationship_type="전체 흐름 (추상→1차→2차)", selected_primary_tag="전체"):
    """Sankey 다이어그램 생성"""
    import plotly.graph_objects as go

    # 관계 타입에 따른 데이터 필터링
    filtered_abs_to_prim = {}
    filtered_prim_to_sec = {}

    if relationship_type == "1차→2차만":
        # 1차→2차 관계만 표시
        if selected_primary_tag != "전체":
            filtered_prim_to_sec = {k: v for k, v in relationships['primary_to_secondary'].items()
                                  if k[0] == selected_primary_tag and v >= min_frequency}
        else:
            filtered_prim_to_sec = {k: v for k, v in relationships['primary_to_secondary'].items() if v >= min_frequency}

    elif relationship_type == "추상→1차만":
        # 추상→1차 관계만 표시
        if selected_abstract_tag != "전체":
            filtered_abs_to_prim = {k: v for k, v in relationships['abstract_to_primary'].items()
                                  if k[0] == selected_abstract_tag and v >= min_frequency}
        else:
            filtered_abs_to_prim = {k: v for k, v in relationships['abstract_to_primary'].items() if v >= min_frequency}

    else:  # "전체 흐름 (추상→1차→2차)"
        # 추상 태그 필터 적용
        if selected_abstract_tag != "전체":
            # 선택된 추상 태그와 연결된 관계만 필터링
            for (abs_tag, prim_tag), count in relationships['abstract_to_primary'].items():
                if abs_tag == selected_abstract_tag and count >= min_frequency:
                    filtered_abs_to_prim[(abs_tag, prim_tag)] = count

            # 필터링된 1차 태그들과 연결된 2차 태그 관계 찾기
            connected_primary_tags = set(prim_tag for (abs_tag, prim_tag) in filtered_abs_to_prim.keys())
            for (prim_tag, sec_tag), count in relationships['primary_to_secondary'].items():
                if prim_tag in connected_primary_tags and count >= min_frequency:
                    filtered_prim_to_sec[(prim_tag, sec_tag)] = count
        else:
            # 전체 보기: 최소 빈도만 적용
            filtered_abs_to_prim = {k: v for k, v in relationships['abstract_to_primary'].items() if v >= min_frequency}
            filtered_prim_to_sec = {k: v for k, v in relationships['primary_to_secondary'].items() if v >= min_frequency}

    # 실제 사용되는 노드만 추출
    used_abstract_tags = set()
    used_primary_tags = set()
    used_secondary_tags = set()

    for (abs_tag, prim_tag) in filtered_abs_to_prim.keys():
        used_abstract_tags.add(abs_tag)
        used_primary_tags.add(prim_tag)

    for (prim_tag, sec_tag) in filtered_prim_to_sec.keys():
        used_primary_tags.add(prim_tag)
        used_secondary_tags.add(sec_tag)

    # 노드를 빈도순으로 정렬
    def sort_by_frequency(tags, relationships, is_source=True):
        """태그들을 관계 빈도순으로 정렬"""
        tag_frequency = {}

        for (source_tag, target_tag), count in relationships.items():
            if is_source:
                # source 태그의 총 빈도 계산
                if source_tag in tags:
                    tag_frequency[source_tag] = tag_frequency.get(source_tag, 0) + count
            else:
                # target 태그의 총 빈도 계산
                if target_tag in tags:
                    tag_frequency[target_tag] = tag_frequency.get(target_tag, 0) + count

        # 빈도순으로 정렬 (높은 순)
        sorted_tags = sorted(tags, key=lambda x: tag_frequency.get(x, 0), reverse=True)
        return sorted_tags

    # 노드 생성
    all_nodes = []
    node_colors = []

    # 추상 태그 (빈도순 정렬)
    if used_abstract_tags:
        abstract_nodes = sort_by_frequency(used_abstract_tags, filtered_abs_to_prim, is_source=True)
    else:
        abstract_nodes = []
    all_nodes.extend([f"추상: {tag}" for tag in abstract_nodes])
    node_colors.extend(['#1f77b4'] * len(abstract_nodes))

    # 1차 태그 (빈도순 정렬)
    if used_primary_tags:
        # 1차 태그는 추상→1차 관계와 1차→2차 관계 둘 다 고려
        primary_freq = {}
        # 추상→1차에서 target으로서의 빈도
        for (abs_tag, prim_tag), count in filtered_abs_to_prim.items():
            if prim_tag in used_primary_tags:
                primary_freq[prim_tag] = primary_freq.get(prim_tag, 0) + count
        # 1차→2차에서 source로서의 빈도
        for (prim_tag, sec_tag), count in filtered_prim_to_sec.items():
            if prim_tag in used_primary_tags:
                primary_freq[prim_tag] = primary_freq.get(prim_tag, 0) + count

        primary_nodes = sorted(used_primary_tags, key=lambda x: primary_freq.get(x, 0), reverse=True)
    else:
        primary_nodes = []
    all_nodes.extend([f"1차: {tag}" for tag in primary_nodes])
    node_colors.extend(['#2ca02c'] * len(primary_nodes))

    # 2차 태그 (빈도순 정렬)
    if used_secondary_tags:
        secondary_nodes = sort_by_frequency(used_secondary_tags, filtered_prim_to_sec, is_source=False)
    else:
        secondary_nodes = []
    all_nodes.extend([f"2차: {tag}" for tag in secondary_nodes])
    node_colors.extend(['#ff7f0e'] * len(secondary_nodes))

    if not all_nodes:
        st.warning(f"선택된 조건에 맞는 태그 관계가 없습니다. (관계타입: {relationship_type}, 최소빈도: {min_frequency})")
        return

    # 노드 인덱스 맵핑
    node_dict = {node: idx for idx, node in enumerate(all_nodes)}

    # 빈도별 색상 분위수 계산
    def get_frequency_color(frequency, all_frequencies, link_type="abs_to_prim"):
        """빈도 분위수에 따른 색상 반환"""
        import numpy as np

        if not all_frequencies:
            return 'rgba(128, 128, 128, 0.6)'  # 기본 회색

        # 분위수 계산
        q25 = np.percentile(all_frequencies, 25)
        q50 = np.percentile(all_frequencies, 50)
        q75 = np.percentile(all_frequencies, 75)

        # 색상 팔레트 (추상→1차, 1차→2차별로 다른 색상)
        if link_type == "abs_to_prim":
            colors = {
                'Q1': 'rgba(255, 182, 193, 0.7)',  # 연한 핑크 (하위 25%)
                'Q2': 'rgba(255, 105, 180, 0.7)',  # 핫핑크 (25-50%)
                'Q3': 'rgba(220, 20, 60, 0.7)',    # 크림슨 (50-75%)
                'Q4': 'rgba(139, 0, 0, 0.8)'       # 다크레드 (상위 25%)
            }
        else:  # prim_to_sec
            colors = {
                'Q1': 'rgba(173, 216, 230, 0.7)',  # 연한 파랑 (하위 25%)
                'Q2': 'rgba(100, 149, 237, 0.7)',  # 코른플라워 블루 (25-50%)
                'Q3': 'rgba(65, 105, 225, 0.7)',   # 로얄 블루 (50-75%)
                'Q4': 'rgba(25, 25, 112, 0.8)'     # 미드나잇 블루 (상위 25%)
            }

        # 분위수에 따른 색상 결정
        if frequency <= q25:
            return colors['Q1']
        elif frequency <= q50:
            return colors['Q2']
        elif frequency <= q75:
            return colors['Q3']
        else:
            return colors['Q4']

    # 모든 빈도 값 수집 (분위수 계산용)
    abs_to_prim_frequencies = list(filtered_abs_to_prim.values())
    prim_to_sec_frequencies = list(filtered_prim_to_sec.values())

    # 링크 생성
    source = []
    target = []
    value = []
    link_colors = []

    # 추상 → 1차 링크
    for (abs_tag, prim_tag), count in filtered_abs_to_prim.items():
        source.append(node_dict[f"추상: {abs_tag}"])
        target.append(node_dict[f"1차: {prim_tag}"])
        value.append(count)
        color = get_frequency_color(count, abs_to_prim_frequencies, "abs_to_prim")
        link_colors.append(color)

    # 1차 → 2차 링크
    for (prim_tag, sec_tag), count in filtered_prim_to_sec.items():
        source.append(node_dict[f"1차: {prim_tag}"])
        target.append(node_dict[f"2차: {sec_tag}"])
        value.append(count)
        color = get_frequency_color(count, prim_to_sec_frequencies, "prim_to_sec")
        link_colors.append(color)

    # Sankey 다이어그램 생성
    if relationship_type == "1차→2차만":
        title_text = f"태그 관계도: 1차 → 2차 ({selected_primary_tag})" if selected_primary_tag != "전체" else "태그 관계도: 1차 → 2차"
    elif relationship_type == "추상→1차만":
        title_text = f"태그 관계도: 추상 → 1차 ({selected_abstract_tag})" if selected_abstract_tag != "전체" else "태그 관계도: 추상 → 1차"
    else:
        title_text = f"태그 관계도: 전체 흐름 ({selected_abstract_tag})" if selected_abstract_tag != "전체" else "태그 관계도: 전체 흐름"

    # 노드 위치 계산 (관계 타입에 따라)
    node_x = []
    node_y = []

    if relationship_type == "1차→2차만":
        # 1차 태그들 (X=0.01, 왼쪽)
        primary_count = len(primary_nodes)
        for i in range(primary_count):
            node_x.append(0.01)
            node_y.append(0.1 + (0.8 * i / max(1, primary_count - 1)) if primary_count > 1 else 0.5)

        # 2차 태그들 (X=0.99, 오른쪽)
        secondary_count = len(secondary_nodes)
        for i in range(secondary_count):
            node_x.append(0.99)
            node_y.append(0.1 + (0.8 * i / max(1, secondary_count - 1)) if secondary_count > 1 else 0.5)

    elif relationship_type == "추상→1차만":
        # 추상 태그들 (X=0.01, 왼쪽)
        abstract_count = len(abstract_nodes)
        for i in range(abstract_count):
            node_x.append(0.01)
            node_y.append(0.1 + (0.8 * i / max(1, abstract_count - 1)) if abstract_count > 1 else 0.5)

        # 1차 태그들 (X=0.99, 오른쪽)
        primary_count = len(primary_nodes)
        for i in range(primary_count):
            node_x.append(0.99)
            node_y.append(0.1 + (0.8 * i / max(1, primary_count - 1)) if primary_count > 1 else 0.5)

    else:  # "전체 흐름 (추상→1차→2차)"
        # 추상 태그들 (X=0.01, 왼쪽 열)
        abstract_count = len(abstract_nodes)
        for i in range(abstract_count):
            node_x.append(0.01)
            node_y.append(0.1 + (0.8 * i / max(1, abstract_count - 1)) if abstract_count > 1 else 0.5)

        # 1차 태그들 (X=0.5, 중간 열)
        primary_count = len(primary_nodes)
        for i in range(primary_count):
            node_x.append(0.5)
            node_y.append(0.1 + (0.8 * i / max(1, primary_count - 1)) if primary_count > 1 else 0.5)

        # 2차 태그들 (X=0.99, 오른쪽 열)
        secondary_count = len(secondary_nodes)
        for i in range(secondary_count):
            node_x.append(0.99)
            node_y.append(0.1 + (0.8 * i / max(1, secondary_count - 1)) if secondary_count > 1 else 0.5)

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_nodes,
            color=node_colors,
            x=node_x,
            y=node_y
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors
        )
    )])

    fig.update_layout(
        title_text=title_text,
        font_size=12,
        height=800
    )

    st.plotly_chart(fig, use_container_width=True)


    # 통계 정보 표시
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("추상 태그", len(relationships['abstract_tags']))

    with col2:
        st.metric("1차 태그", len(relationships['primary_tags']))

    with col3:
        st.metric("2차 태그", len(relationships['secondary_tags']))

    # 상위 관계 표시
    st.subheader("🔗 주요 태그 관계")

    # 추상→1차 상위 관계
    if relationships['abstract_to_primary']:
        st.write("**추상 → 1차 태그 (상위 10개)**")
        abs_to_prim_sorted = sorted(relationships['abstract_to_primary'].items(),
                                  key=lambda x: x[1], reverse=True)[:10]

        for (abs_tag, prim_tag), count in abs_to_prim_sorted:
            st.write(f"• {abs_tag} → {prim_tag}: {count}회")

    # 1차→2차 상위 관계
    if relationships['primary_to_secondary']:
        st.write("**1차 → 2차 태그 (상위 10개)**")
        prim_to_sec_sorted = sorted(relationships['primary_to_secondary'].items(),
                                  key=lambda x: x[1], reverse=True)[:10]

        for (prim_tag, sec_tag), count in prim_to_sec_sorted:
            st.write(f"• {prim_tag} → {sec_tag}: {count}회")


def render_database_management_sidebar():
    """사이드바에 데이터베이스 관리 기능 렌더링"""
    st.sidebar.write("### 🗄️ 데이터베이스 관리")

    # JSON 파일 스캔
    json_files_path = Path("json_files")
    if json_files_path.exists():
        json_files = list(json_files_path.glob("*.json"))

        if json_files:
            st.sidebar.write(f"📁 `json_files/`에서 {len(json_files)}개 파일 발견")

            # 미리보기
            with st.sidebar.expander("파일 목록 보기"):
                for file_path in json_files[:5]:  # 최대 5개만 표시
                    st.write(f"• {file_path.name}")
                if len(json_files) > 5:
                    st.write(f"... 외 {len(json_files) - 5}개")

            # 데이터베이스 추가 버튼
            if st.sidebar.button("🔄 데이터베이스에 추가",
                               help="json_files/ 폴더의 파일들을 데이터베이스에 영구 저장합니다."):

                with st.spinner("데이터베이스에 추가 중..."):
                    try:
                        # JSON 파일들 로드
                        json_data_list = []
                        failed_files = []

                        for file_path in json_files:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    json_data = json.load(f)
                                    # 파일명 추가 (추적용)
                                    json_data['_filename'] = file_path.name
                                    json_data_list.append(json_data)
                            except Exception as e:
                                failed_files.append(f"{file_path.name}: {e}")
                                st.sidebar.error(f"파일 읽기 오류 {file_path.name}: {e}")

                        # 데이터베이스에 추가
                        if json_data_list:
                            # 임포트 전 카운트
                            initial_count = len(json_data_list)

                            # 임포트 실행
                            import_result = db_manager.import_json_data(json_data_list)

                            # 결과 표시
                            st.sidebar.success(f"✅ 처리 완료!")
                            st.sidebar.info(f"📥 읽기 성공: {initial_count}개")

                            if failed_files:
                                st.sidebar.warning(f"❌ 읽기 실패: {len(failed_files)}개")
                                with st.sidebar.expander("실패한 파일들"):
                                    for failed_file in failed_files:
                                        st.write(f"• {failed_file}")

                            # 중복 체크 정보도 표시하면 좋을 것 같습니다
                            st.sidebar.info(f"💡 중복된 이름의 파일은 자동으로 건너뜁니다.")

                            # 처리된 파일들을 processed 폴더로 이동 (선택사항)
                            processed_path = json_files_path / "processed"
                            processed_path.mkdir(exist_ok=True)

                            moved_count = 0
                            for file_path in json_files:
                                try:
                                    import shutil
                                    shutil.move(str(file_path), str(processed_path / file_path.name))
                                    moved_count += 1
                                except Exception as e:
                                    st.sidebar.warning(f"파일 이동 실패 {file_path.name}: {e}")

                            if moved_count > 0:
                                st.sidebar.info(f"📦 {moved_count}개 파일이 `json_files/processed/`로 이동되었습니다.")

                            # 페이지 새로고침을 위한 hint
                            st.sidebar.info("💡 변경사항을 확인하려면 페이지를 새로고침하세요.")
                        else:
                            st.sidebar.warning("처리할 수 있는 파일이 없습니다.")

                    except Exception as e:
                        st.sidebar.error(f"데이터베이스 추가 중 오류 발생: {e}")
        else:
            st.sidebar.info("📭 `json_files/` 폴더가 비어있습니다.")
    else:
        st.sidebar.info("📁 `json_files/` 폴더가 없습니다.")



if __name__ == "__main__":
    main()
