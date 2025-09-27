"""
태그 분석 및 처리 유틸리티
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json
from .landmark_calculator import calculate_length, calculate_curvature


def get_tag_groups():
    """태그 그룹 정보를 반환합니다."""
    return {
        "추상 - 분위기": ['세련된', '친근한'],
        "추상 - 품격": ['고급스러운', '생기있는'],
        "추상 - 시대감": ['현대적인','고전적인'],
        "추상 - 신뢰감": ['선한','날티나는'],
        "1차 - 동물상": ['강아지','고양이','다람쥐','참새','사슴','토끼','꼬부기','사막여우','호랑이'],
        "1차 - 지역감": ['서구적인','동양적인'],
        "1차 - 성별감": ['남성적','중성적','여성스런'],
        "1차 - 매력": ['귀여운', '청순한', '섹시한'],
        "1차 - 연령감": ['동안의', '성숙한'],
        "1차 - 화려함": ['화려한','수수한'],
        "1차 - 온도감": ['차가운','따뜻한'],
        "1차 - 성격": ['지적인','발랄한'],
        "1차 - 인상": ['날카로운','부드러운'],
        "1차 - 얼굴형": ['진한','두부상'],
        "2차 - 이마": ['forehead-높이-긴', 'forehead-높이-보통', 'forehead-높이-짧은', 'forehead-너비-넓은', 'forehead-너비-보통', 'forehead-너비-좁은'],
        "2차 - 눈썹": ['eyebrow-눈과의거리-먼', 'eyebrow-눈과의거리-보통', 'eyebrow-눈과의거리-가까운', 'eyebrow-형태-공격', 'eyebrow-형태-아치', 'eyebrow-형태-물결', 'eyebrow-형태-일자', 'eyebrow-형태-둥근', 'eyebrow-형태-처진', 'eyebrow-곡률-큰', 'eyebrow-곡률-보통', 'eyebrow-곡률-작은', 'eyebrow-거리-먼', 'eyebrow-거리-보통', 'eyebrow-거리-가까운', 'eyebrow-길이-긴', 'eyebrow-길이-보통', 'eyebrow-길이-짧은', 'eyebrow-두께-두꺼운', 'eyebrow-두께-보통', 'eyebrow-두께-얇은', 'eyebrow-숱-진한', 'eyebrow-숱-보통', 'eyebrow-숱-흐린'],
        "2차 - 눈": ['eye-인상-사나운', 'eye-인상-똘망똘망한', 'eye-인상-보통', 'eye-인상-순한', 'eye-인상-졸린', 'eye-미간-먼', 'eye-미간-보통', 'eye-미간-좁은', 'eye-모양-시원한', 'eye-모양-찢어진', 'eye-모양-보통', 'eye-모양-동그란', 'eye-모양-답답한', 'eye-길이-긴', 'eye-길이-보통', 'eye-길이-짧은', 'eye-높이-높은', 'eye-높이-보통', 'eye-높이-낮은', 'eye-쌍꺼풀-없음', 'eye-쌍꺼풀-아웃', 'eye-쌍꺼풀-세미아웃', 'eye-쌍꺼풀-인아웃', 'eye-쌍꺼풀-인', 'eye-애교-많은', 'eye-애교-보통', 'eye-애교-적은', 'eye-눈밑지-심한', 'eye-눈밑지-약간', 'eye-눈밑지-없음'],
        "2차 - 코": ['nose-모양-화살코', 'nose-모양-보통', 'nose-모양-복코', 'nose-모양-들창코', 'nose-길이-긴', 'nose-길이-보통', 'nose-길이-짧은', 'nose-콧대-두꺼운', 'nose-콧대-보통', 'nose-콧대-얇은', 'nose-콧볼-넓은', 'nose-콧볼-보통', 'nose-콧볼-좁은', 'nose-코끝-넓은', 'nose-코끝-보통', 'nose-코끝-좁은', 'nose-콧구멍-큰', 'nose-콧구멍-긴', 'nose-콧구멍-보통', 'nose-콧구멍-작은'],
        "2차 - 입": ['mouth-너비-넓은', 'mouth-너비-보통', 'mouth-너비-좁은', 'mouth-두께-두꺼운', 'mouth-두께-도톰', 'mouth-두께-보통', 'mouth-두께-얇은', 'mouth-입꼬리-올라간', 'mouth-입꼬리-평평한', 'mouth-입꼴-내려간', 'mouth-위두께-두꺼운', 'mouth-위두께-보통', 'mouth-위두께-얇은', 'mouth-아래두께-두꺼운', 'mouth-아래두께-보통', 'mouth-아래두께-얇은', 'mouth-전체입술선-또렷', 'mouth-전체입술선-보통', 'mouth-전체입술선-흐릿', 'mouth-큐피드-또렷', 'mouth-큐피드-둥글', 'mouth-큐피드-1자', 'mouth-입술결절-뾰족', 'mouth-입술결절-1자', 'mouth-입술결절-함몰', 'mouth-중심-위', 'mouth-중심-중간', 'mouth-중심-아래', 'mouth-인중길이-짧아', 'mouth-인중길이-보통', 'mouth-인중길이-길어', 'mouth-인중너비-넓어', 'mouth-인중너비-보통', 'mouth-인중너비-좁아', 'mouth-팔자-깊은', 'mouth-팔자-보통', 'mouth-팔자-없음'],
        "2차 - 윤곽": ['silhouette-얼굴형-달걀형', 'silhouette-얼굴형-역삼각형', 'silhouette-얼굴형-긴', 'silhouette-얼굴형-동글', 'silhouette-얼굴형-사각형', 'silhouette-옆광대-높이-높은', 'silhouette-옆광대-높이-보통', 'silhouette-옆광대-높이-낮은', 'silhouette-옆광대-위치-밖', 'silhouette-옆광대-위치-보통', 'silhouette-옆광대-위치-안', 'silhouette-앞광대-크기-큰', 'silhouette-앞광대-크기-보통', 'silhouette-앞광대-크기-작은', 'silhouette-앞광대-높이-높은', 'silhouette-앞광대-높이-보통', 'silhouette-앞광대-높이-낮은', 'silhouette-턱형태-발달', 'silhouette-턱형태-뾰족', 'silhouette-턱형태-보통', 'silhouette-턱형태-무턱', 'silhouette-턱-길이-긴', 'silhouette-턱-길이-보통', 'silhouette-턱-길이-짧은', 'silhouette-볼-살-살X', 'silhouette-볼-살-보통', 'silhouette-볼-살-살O'],
    }


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


def execute_single_tag_analysis(landmarks_data, selected_tag, point1, point2, calc_type):
    """단일 태그 분석 실행"""
    st.write("### 🔄 분석 실행 중...")

    # 선택된 태그를 가진 데이터 필터링
    tag_data = []
    all_data = []
    names_with_tag = []
    names_all = []

    for _, row in landmarks_data.iterrows():
        try:
            # 랜드마크 데이터 파싱
            if isinstance(row['landmarks'], str):
                landmarks = json.loads(row['landmarks'])
            else:
                landmarks = row['landmarks']

            # 측정값 계산
            measurement = calculate_length(landmarks, point1, point2, calc_type)

            if measurement is not None:
                all_data.append(measurement)
                names_all.append(row['name'])

                # 선택된 태그를 가진 데이터인지 확인
                if 'tags' in row and row['tags']:
                    row_tags = row['tags'] if isinstance(row['tags'], list) else []
                    if selected_tag in row_tags:
                        tag_data.append(measurement)
                        names_with_tag.append(row['name'])

        except Exception as e:
            continue

    if not tag_data:
        st.error(f"'{selected_tag}' 태그를 가진 데이터가 없습니다.")
        return

    # 통계 계산
    tag_mean = np.mean(tag_data)
    tag_std = np.std(tag_data)
    tag_q1, tag_q3 = np.percentile(tag_data, [25, 75])

    all_mean = np.mean(all_data)
    all_std = np.std(all_data)

    # 경계값 제안 (Q1 기준)
    boundary_suggestion = tag_q1

    # 결과 표시
    st.write("### 📊 분석 결과")

    # 상단 메트릭
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("분석 태그", selected_tag)
    with col2:
        st.metric("태그 데이터", f"{len(tag_data)}개")
    with col3:
        st.metric("전체 데이터", f"{len(all_data)}개")
    with col4:
        st.metric("제안 경계값", f"{boundary_suggestion:.2f}")

    # 박스플롯 생성
    col1, col2 = st.columns([2, 1])

    with col1:
        # 데이터 준비
        plot_data = []
        for val in tag_data:
            plot_data.append({'value': val, 'group': f'{selected_tag} ({len(tag_data)}개)'})
        for val in all_data:
            plot_data.append({'value': val, 'group': f'전체 데이터 ({len(all_data)}개)'})

        plot_df = pd.DataFrame(plot_data)

        fig = px.box(
            plot_df,
            x='group',
            y='value',
            title=f'{selected_tag} vs 전체 데이터 분포',
            labels={'value': f'측정값 ({calc_type})', 'group': '그룹'}
        )

        # 경계선 추가
        fig.add_hline(y=boundary_suggestion, line_dash="dash", line_color="red",
                     annotation_text=f"제안 경계값: {boundary_suggestion:.2f}")

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("#### 📈 태그 그룹 통계")
        st.write(f"**평균:** {tag_mean:.3f}")
        st.write(f"**표준편차:** {tag_std:.2f}")
        st.write(f"**Q1:** {tag_q1:.2f}")
        st.write(f"**Q3:** {tag_q3:.2f}")

        st.write("#### 📈 전체 데이터 통계")
        st.write(f"**평균:** {all_mean:.3f}")
        st.write(f"**표준편차:** {all_std:.2f}")

        # 차이 분석
        mean_diff = tag_mean - all_mean
        st.write("#### 🔍 차이 분석")
        st.write(f"**평균 차이:** {mean_diff:+.2f}")

        if abs(mean_diff) > all_std:
            st.success("✅ 의미있는 차이 (1σ 이상)")
        else:
            st.warning("⚠️ 작은 차이 (1σ 미만)")

    # 경계값 제안
    st.write("### 🎯 경계값 제안")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**보수적 기준 (Q1)**")
        st.write(f"{tag_q1:.2f} 이상")
        st.write(f"정확도: ~75%")

    with col2:
        st.write("**중간 기준 (평균)**")
        st.write(f"{tag_mean:.2f} 이상")
        st.write(f"정확도: ~50%")

    with col3:
        st.write("**관대한 기준 (Q3)**")
        st.write(f"{tag_q3:.2f} 이상")
        st.write(f"정확도: ~25%")

    # 상세 데이터
    with st.expander("📋 상세 데이터 보기"):
        detail_df = pd.DataFrame({
            '파일명': names_with_tag,
            '측정값': tag_data
        })
        detail_df = detail_df.sort_values('측정값', ascending=False)
        st.dataframe(detail_df, use_container_width=True)


def execute_level_comparison_analysis_ratio(landmarks_data, selected_feature, point1, point2, calc_type1, point3, point4, calc_type2):
    """레벨별 비교 분석 실행 (비율 계산)"""

    # 해당 특성의 모든 레벨 태그 찾기
    tag_groups = get_tag_groups()
    feature_levels = {}

    for group_name, tags in tag_groups.items():
        if group_name.startswith("2차"):
            for tag in tags:
                if tag.startswith(selected_feature + "-"):
                    level = tag.split('-')[-1]
                    feature_levels[level] = tag

    # 각 레벨별 데이터 수집
    level_data = {}
    level_names = {}
    level_numerators = {}  # 분자 값들
    level_denominators = {}  # 분모 값들

    for level, full_tag in feature_levels.items():
        level_data[level] = []
        level_names[level] = []
        level_numerators[level] = []
        level_denominators[level] = []

        for _, row in landmarks_data.iterrows():
            try:
                # 랜드마크 데이터 파싱
                if isinstance(row['landmarks'], str):
                    landmarks = json.loads(row['landmarks'])
                else:
                    landmarks = row['landmarks']

                # 분자 길이 계산
                numerator = calculate_length(landmarks, point1, point2, calc_type1)
                # 분모 길이 계산
                denominator = calculate_length(landmarks, point3, point4, calc_type2)

                if numerator is not None and denominator is not None and denominator != 0:
                    # 비율 계산
                    ratio = numerator / denominator

                    # 해당 레벨 태그를 가진 데이터인지 확인
                    if 'tags' in row and row['tags']:
                        row_tags = row['tags'] if isinstance(row['tags'], list) else []
                        if full_tag in row_tags:
                            level_data[level].append(ratio)
                            level_names[level].append(row['name'])
                            level_numerators[level].append(numerator)
                            level_denominators[level].append(denominator)

            except Exception as e:
                continue

    # 데이터가 있는 레벨만 필터링
    valid_levels = {level: data for level, data in level_data.items() if len(data) > 0}

    if len(valid_levels) < 2:
        st.error("비교할 수 있는 레벨이 부족합니다. (최소 2개 레벨 필요)")
        return

    # 결과 표시
    st.write("### 📊 레벨별 비교 결과 (비율)")

    # 레벨별 통계 계산
    level_stats = {}

    for level, data in valid_levels.items():
        level_mean = np.mean(data)
        level_stats[level] = {
            'mean': level_mean,
            'std': np.std(data),
            'q1': np.percentile(data, 25),
            'q3': np.percentile(data, 75),
            'count': len(data)
        }

    # 데이터 준비 (파일명 및 분자/분모 포함)
    plot_data = []
    all_values = []
    actual_labels = []
    file_names = []
    all_numerators = []
    all_denominators = []

    for level, data in valid_levels.items():
        for idx, val in enumerate(data):
            file_name = level_names[level][idx]
            numerator = level_numerators[level][idx]
            denominator = level_denominators[level][idx]

            plot_data.append({
                'value': val,
                'level': f'{level} ({len(data)}개)',
                'name': file_name,
                'numerator': numerator,
                'denominator': denominator
            })
            all_values.append(val)
            actual_labels.append(level)
            file_names.append(file_name)
            all_numerators.append(numerator)
            all_denominators.append(denominator)

    plot_df = pd.DataFrame(plot_data)

    # 통계 요약 (모든 정보를 1행에 통합)
    st.write("### 📈 통계 요약")

    # 레벨을 평균값 순으로 정렬
    sorted_levels = sorted(level_stats.items(), key=lambda x: x[1]['mean'])

    # 경계값 개수 계산
    num_boundaries = len(sorted_levels) - 1 if len(sorted_levels) >= 2 else 0

    # 전체 컬럼 수 = 레벨 수 + 경계값 수
    total_cols = len(valid_levels) + num_boundaries
    all_cols = st.columns(total_cols)

    # 경계값들을 가장 왼쪽에 먼저 배치
    col_idx = 0
    if len(sorted_levels) >= 2:
        for i in range(len(sorted_levels) - 1):
            level1_name, level1_stats = sorted_levels[i]
            level2_name, level2_stats = sorted_levels[i + 1]

            # 중간값으로 경계 설정
            boundary = (level1_stats['q3'] + level2_stats['q1']) / 2

            with all_cols[col_idx]:
                st.metric(
                    label=f"경계값 제시: {level1_name} ↔ {level2_name}",
                    value=f"{boundary:.3f}"
                )
            col_idx += 1

    # 레벨별 통계를 경계값 다음에 배치
    for level, stats in level_stats.items():
        with all_cols[col_idx]:
            st.metric(
                label=f"{level} ({stats['count']}개)",
                value=f"{stats['mean']:.3f}",
                delta=f"Q1-Q3: {stats['q1']:.3f}-{stats['q3']:.3f}"
            )
        col_idx += 1

    # 세로 배치 (K-means → KDE → 히스토그램 → 박스플롯)

    # 1. K-means 클러스터링 (분모 vs 분자)
    st.write("#### 🎯 분모-분자 관계 (K-means)")

    try:
        from sklearn.cluster import KMeans

        if len(all_values) > len(valid_levels):  # 클러스터 수보다 많은 데이터가 있어야 함
            # 2차원 K-means 클러스터링 (분모, 분자)
            X = np.column_stack([all_denominators, all_numerators])
            n_clusters = len(valid_levels)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X)

            # 산점도 데이터 준비
            scatter_data = pd.DataFrame({
                'denominator': all_denominators,
                'numerator': all_numerators,
                'ratio': all_values,
                'actual_level': actual_labels,
                'cluster': [f'클러스터 {i}' for i in cluster_labels],
                'name': file_names
            })

            # 개선된 색상 팔레트와 마커 심볼 정의 (빨강 제외 - 중심점 전용)
            n_clusters = len(valid_levels)
            if n_clusters == 3:
                cluster_colors = ['#1f77b4', '#2ca02c', '#9467bd']  # 파랑-초록-보라
            elif n_clusters == 4:
                cluster_colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']  # 파랑-초록-주황-보라
            else:
                # 5개 이상일 때는 빨강 제외한 구분 잘되는 색상들
                cluster_colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#f7b6d3']

            # 마커 심볼 개선 (원-X-세모-별-네모-...)
            cluster_symbols = ['circle', 'x', 'triangle-up', 'star', 'square', 'diamond', 'cross', 'triangle-down', 'pentagon', 'hexagon']

            fig_cluster = px.scatter(
                scatter_data,
                x='denominator',
                y='numerator',
                color='actual_level',
                symbol='cluster',
                title=f'{selected_feature} 분모-분자 관계 (K-means)',
                labels={'denominator': f'분모 ({calc_type2})', 'numerator': f'분자 ({calc_type1})'},
                hover_data=['name', 'actual_level', 'cluster', 'ratio'],
                color_discrete_sequence=cluster_colors[:len(valid_levels)],
                symbol_sequence=cluster_symbols[:n_clusters]
            )

            # 일반 마커 크기 1씩 증가
            fig_cluster.update_traces(marker_size=7)

            # 축 범위 자동 조정
            x_min, x_max = min(all_denominators), max(all_denominators)
            y_min, y_max = min(all_numerators), max(all_numerators)

            # 여백 추가 (5%)
            x_margin = (x_max - x_min) * 0.05
            y_margin = (y_max - y_min) * 0.05

            # 축 범위 설정
            fig_cluster.update_xaxes(range=[x_min - x_margin, x_max + x_margin])
            fig_cluster.update_yaxes(range=[y_min - y_margin, y_max + y_margin])

            # 클러스터 중심점 표시 (각 클러스터와 같은 모양, 빨강 색상)
            for i, center in enumerate(kmeans.cluster_centers_):
                fig_cluster.add_scatter(
                    x=[center[0]],
                    y=[center[1]],
                    mode='markers',
                    marker=dict(
                        symbol=cluster_symbols[i % len(cluster_symbols)],  # 클러스터와 같은 모양
                        size=12,  # 더 큰 크기
                        color='#d62728',  # 빨강 (중심점 전용)
                        line=dict(width=3, color='#d62728')
                    ),
                    name=f'중심{i+1}',
                    showlegend=True
                )

            # 동일 비율선들 추가 (참고용)
            x_range_line = np.linspace(x_min - x_margin, x_max + x_margin, 100)

            # 실제 비율 범위 계산
            actual_ratios = [val for val in all_values]
            min_ratio, max_ratio = min(actual_ratios), max(actual_ratios)

            # 적절한 비율선 선택
            ratio_lines = []
            for ratio in [0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]:
                if min_ratio * 0.5 <= ratio <= max_ratio * 2.0:
                    ratio_lines.append(ratio)

            for ratio in ratio_lines:
                y_line = ratio * x_range_line
                # Y축 범위 내에서만 표시
                mask = (y_line >= y_min - y_margin) & (y_line <= y_max + y_margin)
                if np.any(mask):
                    fig_cluster.add_scatter(
                        x=x_range_line[mask],
                        y=y_line[mask],
                        mode='lines',
                        line=dict(dash='dot', color='gray', width=1),
                        opacity=0.5,
                        name=f'비율 {ratio}',
                        showlegend=False,
                        hoverinfo='skip'
                    )

            st.plotly_chart(fig_cluster, use_container_width=True)

        else:
            st.warning("K-means를 위해 더 많은 데이터가 필요합니다.")

    except ImportError:
        st.warning("scikit-learn 라이브러리가 필요합니다.")

    # 2. KDE 곡선
    st.write("#### 🌊 KDE 곡선")
    try:
        from scipy import stats
        fig_kde = go.Figure()

        colors = px.colors.qualitative.Set1
        for i, (level, data) in enumerate(valid_levels.items()):
            if len(data) > 1:  # KDE는 최소 2개 이상의 데이터 필요
                # KDE 계산
                kde = stats.gaussian_kde(data)
                x_range = np.linspace(min(data) - 0.1, max(data) + 0.1, 100)
                density = kde(x_range)

                fig_kde.add_trace(go.Scatter(
                    x=x_range,
                    y=density,
                    mode='lines',
                    name=f'{level} ({len(data)}개)',
                    line=dict(color=colors[i % len(colors)], width=2),
                    fill='tonexty' if i > 0 else 'tozeroy',
                    fillcolor=f'rgba({colors[i % len(colors)][4:-1]}, 0.3)'
                ))

        fig_kde.update_layout(
            title=f'{selected_feature} 레벨별 비율 KDE 확률밀도',
            xaxis_title=f'비율 ({calc_type1}/{calc_type2})',
            yaxis_title='확률밀도'
        )
        st.plotly_chart(fig_kde, use_container_width=True)

    except ImportError:
        st.warning("scipy 라이브러리가 필요합니다.")

    # 3. 히스토그램
    st.write("#### 📊 히스토그램")
    fig_hist = px.histogram(
        plot_df,
        x='value',
        color='level',
        title=f'{selected_feature} 레벨별 비율 히스토그램',
        labels={'value': f'비율 ({calc_type1}/{calc_type2})', 'count': '빈도'},
        marginal='rug',
        opacity=0.7,
        hover_data=['name']
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # 4. 박스플롯
    st.write("#### 📦 박스플롯")
    fig_box = px.box(
        plot_df,
        x='level',
        y='value',
        title=f'{selected_feature} 레벨별 비율 분포 비교',
        labels={'value': f'비율 ({calc_type1}/{calc_type2})', 'level': '레벨'},
        hover_data=['name']
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # 상세 데이터
    with st.expander("📋 레벨별 상세 데이터"):
        for level, data in valid_levels.items():
            st.write(f"#### {level} 레벨")
            detail_df = pd.DataFrame({
                '파일명': level_names[level],
                '비율값': data
            })
            detail_df = detail_df.sort_values('비율값', ascending=False)
            st.dataframe(detail_df, use_container_width=True)


def execute_level_comparison_analysis(landmarks_data, selected_feature, point1, point2, calc_type):
    """레벨별 비교 분석 실행"""

    # 해당 특성의 모든 레벨 태그 찾기
    tag_groups = get_tag_groups()
    feature_levels = {}

    for group_name, tags in tag_groups.items():
        if group_name.startswith("2차"):
            for tag in tags:
                if tag.startswith(selected_feature + "-"):
                    level = tag.split('-')[-1]
                    feature_levels[level] = tag

    # 각 레벨별 데이터 수집
    level_data = {}
    level_names = {}

    for level, full_tag in feature_levels.items():
        level_data[level] = []
        level_names[level] = []

        for _, row in landmarks_data.iterrows():
            try:
                # 랜드마크 데이터 파싱
                if isinstance(row['landmarks'], str):
                    landmarks = json.loads(row['landmarks'])
                else:
                    landmarks = row['landmarks']

                # 측정값 계산
                measurement = calculate_length(landmarks, point1, point2, calc_type)

                if measurement is not None:
                    # 해당 레벨 태그를 가진 데이터인지 확인
                    if 'tags' in row and row['tags']:
                        row_tags = row['tags'] if isinstance(row['tags'], list) else []
                        if full_tag in row_tags:
                            level_data[level].append(measurement)
                            level_names[level].append(row['name'])

            except Exception as e:
                continue

    # 데이터가 있는 레벨만 필터링
    valid_levels = {level: data for level, data in level_data.items() if len(data) > 0}

    if len(valid_levels) < 2:
        st.error("비교할 수 있는 레벨이 부족합니다. (최소 2개 레벨 필요)")
        return

    # 결과 표시
    st.write("### 📊 레벨별 비교 결과")

    # 레벨별 통계 계산
    level_stats = {}

    for level, data in valid_levels.items():
        level_mean = np.mean(data)
        level_stats[level] = {
            'mean': level_mean,
            'std': np.std(data),
            'q1': np.percentile(data, 25),
            'q3': np.percentile(data, 75),
            'count': len(data)
        }

    # 데이터 준비 (파일명 포함)
    plot_data = []
    all_values = []
    actual_labels = []
    file_names = []

    for level, data in valid_levels.items():
        for idx, val in enumerate(data):
            file_name = level_names[level][idx]
            plot_data.append({
                'value': val,
                'level': f'{level} ({len(data)}개)',
                'name': file_name
            })
            all_values.append(val)
            actual_labels.append(level)
            file_names.append(file_name)

    plot_df = pd.DataFrame(plot_data)

    # 통계 요약 (모든 정보를 1행에 통합)
    st.write("### 📈 통계 요약")

    # 레벨을 평균값 순으로 정렬
    sorted_levels = sorted(level_stats.items(), key=lambda x: x[1]['mean'])

    # 경계값 개수 계산
    num_boundaries = len(sorted_levels) - 1 if len(sorted_levels) >= 2 else 0

    # 전체 컬럼 수 = 레벨 수 + 경계값 수
    total_cols = len(valid_levels) + num_boundaries
    all_cols = st.columns(total_cols)

    # 경계값들을 가장 왼쪽에 먼저 배치
    col_idx = 0
    if len(sorted_levels) >= 2:
        for i in range(len(sorted_levels) - 1):
            level1_name, level1_stats = sorted_levels[i]
            level2_name, level2_stats = sorted_levels[i + 1]

            # 중간값으로 경계 설정
            boundary = (level1_stats['q3'] + level2_stats['q1']) / 2

            with all_cols[col_idx]:
                st.metric(
                    label=f"경계값 제시: {level1_name} ↔ {level2_name}",
                    value=f"{boundary:.2f}"
                )
            col_idx += 1

    # 레벨별 통계를 경계값 다음에 배치
    for level, stats in level_stats.items():
        with all_cols[col_idx]:
            st.metric(
                label=f"{level} ({stats['count']}개)",
                value=f"{stats['mean']:.3f}",
                delta=f"Q1-Q3: {stats['q1']:.2f}-{stats['q3']:.2f}"
            )
        col_idx += 1

    # 세로 배치 (K-means → KDE → 히스토그램 → 박스플롯)
    st.write("### 📊 다각도 분석 시각화")

    # 1. K-means 클러스터링
    st.write("#### 🎯 K-means 클러스터링")
    try:
        from sklearn.cluster import KMeans

        if len(all_values) > len(valid_levels):  # 클러스터 수보다 많은 데이터가 있어야 함
            # K-means 클러스터링 (클러스터 수 = 레벨 수)
            X = np.array(all_values).reshape(-1, 1)
            n_clusters = len(valid_levels)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X)

            # 산점도 데이터 준비
            scatter_data = pd.DataFrame({
                'value': all_values,
                'actual_level': actual_labels,
                'cluster': [f'클러스터 {i}' for i in cluster_labels],
                'name': file_names,
                'y_jitter': np.random.uniform(-0.1, 0.1, len(all_values))
            })

            # 개선된 색상 팔레트와 마커 심볼 정의 (빨강 제외 - 중심점 전용)
            n_clusters = len(valid_levels)
            if n_clusters == 3:
                cluster_colors = ['#1f77b4', '#2ca02c', '#9467bd']  # 파랑-초록-보라
            elif n_clusters == 4:
                cluster_colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']  # 파랑-초록-주황-보라
            else:
                # 5개 이상일 때는 빨강 제외한 구분 잘되는 색상들
                cluster_colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#f7b6d3']

            # 마커 심볼 개선 (원-X-세모-별-네모-...)
            cluster_symbols = ['circle', 'x', 'triangle-up', 'star', 'square', 'diamond', 'cross', 'triangle-down', 'pentagon', 'hexagon']

            fig_cluster = px.scatter(
                scatter_data,
                x='value',
                y='y_jitter',
                color='actual_level',
                symbol='cluster',
                title=f'{selected_feature} K-means vs 실제 레벨',
                labels={'value': f'측정값 ({calc_type})', 'y_jitter': ''},
                hover_data=['name', 'actual_level', 'cluster'],
                color_discrete_sequence=cluster_colors[:len(valid_levels)],
                symbol_sequence=cluster_symbols[:n_clusters]
            )

            # 일반 마커 크기 1씩 증가
            fig_cluster.update_traces(marker_size=7)

            # 클러스터 중심점 표시 (빨강 수직선 - 클러스터별 구분)
            line_styles = ["dash", "dot", "dashdot", "solid", "longdash", "longdashdot"]
            for i, center in enumerate(kmeans.cluster_centers_):
                fig_cluster.add_vline(
                    x=center[0],
                    line_dash=line_styles[i % len(line_styles)],  # 클러스터별 다른 선 스타일
                    line_color="#d62728",  # 빨강 (중심점 전용)
                    line_width=3,  # 더 굵게
                    annotation_text=f"중심{i+1}: {center[0]:.2f}"
                )

            fig_cluster.update_yaxes(showticklabels=False, title_text="")
            st.plotly_chart(fig_cluster, use_container_width=True)

        else:
            st.warning("K-means를 위해 더 많은 데이터가 필요합니다.")

    except ImportError:
        st.warning("scikit-learn 라이브러리가 필요합니다.")

    # 2. KDE 곡선
    st.write("#### 🌊 KDE 곡선")
    try:
        from scipy import stats
        fig_kde = go.Figure()

        colors = px.colors.qualitative.Set1
        for i, (level, data) in enumerate(valid_levels.items()):
            if len(data) > 1:  # KDE는 최소 2개 이상의 데이터 필요
                # KDE 계산
                kde = stats.gaussian_kde(data)
                x_range = np.linspace(min(data) - 0.1, max(data) + 0.1, 100)
                density = kde(x_range)

                fig_kde.add_trace(go.Scatter(
                    x=x_range,
                    y=density,
                    mode='lines',
                    name=f'{level} ({len(data)}개)',
                    line=dict(color=colors[i % len(colors)], width=2),
                    fill='tonexty' if i > 0 else 'tozeroy',
                    fillcolor=f'rgba({colors[i % len(colors)][4:-1]}, 0.3)'
                ))

        fig_kde.update_layout(
            title=f'{selected_feature} 레벨별 KDE 확률밀도',
            xaxis_title=f'측정값 ({calc_type})',
            yaxis_title='확률밀도'
        )
        st.plotly_chart(fig_kde, use_container_width=True)

    except ImportError:
        st.warning("scipy 라이브러리가 필요합니다.")

    # 3. 히스토그램
    st.write("#### 📊 히스토그램")
    fig_hist = px.histogram(
        plot_df,
        x='value',
        color='level',
        title=f'{selected_feature} 레벨별 히스토그램',
        labels={'value': f'측정값 ({calc_type})', 'count': '빈도'},
        marginal='rug',
        opacity=0.7,
        hover_data=['name']
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # 4. 박스플롯
    st.write("#### 📦 박스플롯")
    fig_box = px.box(
        plot_df,
        x='level',
        y='value',
        title=f'{selected_feature} 레벨별 분포 비교',
        labels={'value': f'측정값 ({calc_type})', 'level': '레벨'},
        hover_data=['name']
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # 상세 데이터
    with st.expander("📋 레벨별 상세 데이터"):
        for level, data in valid_levels.items():
            st.write(f"#### {level} 레벨")
            detail_df = pd.DataFrame({
                '파일명': level_names[level],
                '측정값': data
            })
            detail_df = detail_df.sort_values('측정값', ascending=False)
            st.dataframe(detail_df, use_container_width=True)


def execute_level_curvature_analysis(landmarks_data, selected_feature, point_group):
    """레벨별 곡률 패턴 분석 실행"""
    st.write("### 🌊 곡률 패턴 분석 실행 중...")

    tag_groups = get_tag_groups()

    # 선택된 특성의 태그들
    if selected_feature in tag_groups:
        feature_tags = tag_groups[selected_feature]
    else:
        # 그룹명에 없으면 특성명으로 태그들을 찾아보기
        feature_tags = []
        for group_name, tags in tag_groups.items():
            for tag in tags:
                if tag.startswith(selected_feature):
                    feature_tags.append(tag)

        if not feature_tags:
            st.error(f"선택된 특성 '{selected_feature}'이(가) 정의되지 않았습니다.")
            st.info("💡 사용 가능한 특성들:")
            # 사용 가능한 특성명들 표시
            available_features = set()
            for group_name, tags in tag_groups.items():
                st.write(f"**{group_name}**: {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}")
                # 특성명 추출 (예: eyebrow-곡률)
                for tag in tags:
                    if '-' in tag:
                        feature_prefix = '-'.join(tag.split('-')[:-1])  # 마지막 레벨 제거
                        available_features.add(feature_prefix)
            st.write(f"**추출 가능한 특성명**: {', '.join(sorted(available_features))}")
            return
        else:
            st.success(f"특성 '{selected_feature}'에서 {len(feature_tags)}개 태그를 찾았습니다: {', '.join(feature_tags)}")

    # 각 레벨별 곡률 데이터 수집
    level_curvatures = {}  # {level: {face_name: [curvature_values]}}
    level_names = {}  # {level: [face_names]}

    for _, row in landmarks_data.iterrows():
        try:
            # 랜드마크 데이터 파싱
            if isinstance(row['landmarks'], str):
                landmarks = json.loads(row['landmarks'])
            else:
                landmarks = row['landmarks']

            # 태그 확인
            if 'tags' in row and row['tags']:
                row_tags = row['tags'] if isinstance(row['tags'], list) else []

                # 선택된 특성의 태그가 있는지 확인
                for tag in feature_tags:
                    if tag in row_tags:
                        # 곡률 계산
                        curvatures = calculate_curvature(landmarks, point_group)
                        if curvatures is not None:
                            if tag not in level_curvatures:
                                level_curvatures[tag] = {}
                                level_names[tag] = []

                            level_curvatures[tag][row['name']] = curvatures
                            level_names[tag].append(row['name'])
                        break
        except Exception as e:
            st.error(f"데이터 처리 오류 ({row['name']}): {e}")
            continue

    # 유효한 레벨만 필터링
    valid_levels = {level: data for level, data in level_curvatures.items() if data}

    if not valid_levels:
        st.error("❌ 분석할 수 있는 데이터가 없습니다.")
        return

    st.write("### 📊 곡률 패턴 분석 결과")

    # 탭으로 구분된 시각화
    tab1, tab2, tab3 = st.tabs(["패턴 오버레이", "점별 분포", "유사도 분석"])

    with tab1:
        render_curvature_overlay_patterns(valid_levels, point_group, selected_feature)

    with tab2:
        render_curvature_point_distributions(valid_levels, point_group, selected_feature)

    with tab3:
        render_curvature_similarity_analysis(valid_levels, point_group, selected_feature)


def render_curvature_overlay_patterns(valid_levels, point_group, selected_feature):
    """곡률 패턴 오버레이 그래프"""
    st.write("#### 🌊 태그별 곡률 패턴 오버레이")

    # 색상 팔레트
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

    fig = go.Figure()

    point_indices = list(range(len(point_group)))

    # 각 레벨별로 처리
    for level_idx, (level, face_curvatures) in enumerate(valid_levels.items()):
        level_color = colors[level_idx % len(colors)]

        # 개별 얼굴들의 곡률 패턴
        for face_name, curvatures in face_curvatures.items():
            fig.add_trace(go.Scatter(
                x=point_indices,
                y=curvatures,
                mode='lines+markers',
                line=dict(color=level_color, width=1.5),
                marker=dict(color=level_color, size=4),
                opacity=0.6,
                name=f"{level}_{face_name}",
                legendgroup=level,
                showlegend=False,
                hovertemplate=f"레벨: {level}<br>얼굴: {face_name}<br>점: %{{x}}<br>곡률: %{{y:.4f}}<extra></extra>"
            ))

        # 평균 패턴 계산
        all_curvatures = list(face_curvatures.values())
        mean_curvatures = np.mean(all_curvatures, axis=0)
        std_curvatures = np.std(all_curvatures, axis=0)

        # 평균선 (굵게)
        fig.add_trace(go.Scatter(
            x=point_indices,
            y=mean_curvatures,
            mode='lines+markers',
            line=dict(color=level_color, width=4),
            marker=dict(color=level_color, size=8, symbol='diamond'),
            name=f"{level} (평균)",
            legendgroup=level,
            hovertemplate=f"레벨: {level} 평균<br>점: %{{x}}<br>곡률: %{{y:.4f}}<extra></extra>"
        ))

        # 신뢰구간
        fig.add_trace(go.Scatter(
            x=point_indices + point_indices[::-1],
            y=(mean_curvatures + std_curvatures).tolist() + (mean_curvatures - std_curvatures).tolist()[::-1],
            fill='toself',
            fillcolor=level_color,
            opacity=0.2,
            line=dict(color='rgba(255,255,255,0)'),
            name=f"{level} (±1σ)",
            legendgroup=level,
            showlegend=False,
            hoverinfo='skip'
        ))

    # y=0 기준선
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7,
                  annotation_text="기준선 (y=0)", annotation_position="bottom right")

    fig.update_layout(
        title=f"{selected_feature} - 곡률 패턴 비교",
        xaxis_title="점 인덱스",
        yaxis_title="곡률 값 (양수: ∩볼록, 음수: ∪오목)",
        hovermode='x unified',
        legend=dict(groupclick="toggleitem")
    )

    st.plotly_chart(fig, use_container_width=True)


def render_curvature_point_distributions(valid_levels, point_group, selected_feature):
    """각 점별 곡률 분포"""
    st.write("#### 📊 점별 곡률 분포")

    num_points = len(point_group)

    # 서브플롯 생성
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=num_points,
        subplot_titles=[f"점 {i} (#{point_group[i]})" for i in range(num_points)],
        shared_yaxes=True
    )

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    for point_idx in range(num_points):
        for level_idx, (level, face_curvatures) in enumerate(valid_levels.items()):
            # 해당 점에서의 곡률값들 수집
            point_curvatures = [curvatures[point_idx] for curvatures in face_curvatures.values()]

            fig.add_trace(
                go.Box(
                    y=point_curvatures,
                    name=level,
                    marker_color=colors[level_idx % len(colors)],
                    legendgroup=level,
                    showlegend=(point_idx == 0),  # 첫 번째 서브플롯에서만 범례 표시
                    boxpoints='all',
                    jitter=0.3,
                    pointpos=-1.8
                ),
                row=1, col=point_idx + 1
            )

    # y=0 기준선들
    for point_idx in range(num_points):
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5,
                      row=1, col=point_idx + 1)

    fig.update_layout(
        title=f"{selected_feature} - 점별 곡률 분포",
        height=400
    )

    fig.update_yaxes(title_text="곡률 값", row=1, col=1)

    st.plotly_chart(fig, use_container_width=True)


def render_curvature_similarity_analysis(valid_levels, point_group, selected_feature):
    """곡률 패턴 유사도 분석"""
    st.write("#### 🔍 곡률 패턴 유사도 분석")

    # 모든 얼굴의 곡률 데이터 평탄화
    all_faces = {}
    face_levels = {}

    for level, face_curvatures in valid_levels.items():
        for face_name, curvatures in face_curvatures.items():
            all_faces[face_name] = curvatures
            face_levels[face_name] = level

    if len(all_faces) < 2:
        st.warning("유사도 분석을 위해서는 최소 2개 이상의 얼굴이 필요합니다.")
        return

    # 유사도 매트릭스 계산 (코사인 유사도)
    face_names = list(all_faces.keys())
    n_faces = len(face_names)
    similarity_matrix = np.zeros((n_faces, n_faces))

    for i, face1 in enumerate(face_names):
        for j, face2 in enumerate(face_names):
            if i == j:
                similarity_matrix[i, j] = 1.0
            else:
                # 코사인 유사도 계산
                vec1 = np.array(all_faces[face1])
                vec2 = np.array(all_faces[face2])

                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)

                if norm1 > 0 and norm2 > 0:
                    similarity = np.dot(vec1, vec2) / (norm1 * norm2)
                else:
                    similarity = 0

                similarity_matrix[i, j] = similarity

    # 히트맵 생성
    fig = px.imshow(
        similarity_matrix,
        x=face_names,
        y=face_names,
        color_continuous_scale='RdYlBu_r',
        title=f"{selected_feature} - 곡률 패턴 유사도 매트릭스",
        labels={'color': '유사도'},
        zmin=-1, zmax=1
    )

    # 텍스트 추가
    for i in range(n_faces):
        for j in range(n_faces):
            fig.add_annotation(
                x=j, y=i,
                text=f"{similarity_matrix[i, j]:.2f}",
                showarrow=False,
                font=dict(color="white" if abs(similarity_matrix[i, j]) > 0.5 else "black")
            )

    fig.update_layout(height=max(400, n_faces * 30))
    st.plotly_chart(fig, use_container_width=True)

    # 유사도 통계
    col1, col2, col3 = st.columns(3)

    # 같은 태그 내 평균 유사도
    same_tag_similarities = []
    diff_tag_similarities = []

    for i, face1 in enumerate(face_names):
        for j, face2 in enumerate(face_names):
            if i < j:  # 중복 제거
                if face_levels[face1] == face_levels[face2]:
                    same_tag_similarities.append(similarity_matrix[i, j])
                else:
                    diff_tag_similarities.append(similarity_matrix[i, j])

    with col1:
        if same_tag_similarities:
            st.metric("같은 태그 내 평균 유사도", f"{np.mean(same_tag_similarities):.3f}")
        else:
            st.metric("같은 태그 내 평균 유사도", "N/A")

    with col2:
        if diff_tag_similarities:
            st.metric("다른 태그 간 평균 유사도", f"{np.mean(diff_tag_similarities):.3f}")
        else:
            st.metric("다른 태그 간 평균 유사도", "N/A")

    with col3:
        if same_tag_similarities and diff_tag_similarities:
            separation = np.mean(same_tag_similarities) - np.mean(diff_tag_similarities)
            st.metric("태그 구분도", f"{separation:.3f}")
        else:
            st.metric("태그 구분도", "N/A")