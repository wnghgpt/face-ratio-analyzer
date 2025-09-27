"""
태그 분석 및 처리 유틸리티
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import json
from .landmark_calculator import calculate_length


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
        "2차 - 입": ['mouth-너비-넓은', 'mouth-너비-보통', 'mouth-너비-좁은', 'mouth-두께-두꺼운', 'mouth-두께-보통', 'mouth-두께-얇은', 'mouth-입꼬리-올라간', 'mouth-입꼬리-평평한', 'mouth-입꼴-내려간', 'mouth-위두께-두꺼운', 'mouth-위두께-보통', 'mouth-위두께-얇은', 'mouth-아래두께-두꺼운', 'mouth-아래두께-보통', 'mouth-아래두께-얇은', 'mouth-전체입술선-또렷', 'mouth-전체입술선-보통', 'mouth-전체입술선-흐릿', 'mouth-큐피드-또렷', 'mouth-큐피드-둥글', 'mouth-큐피드-1자', 'mouth-입술결절-뾰족', 'mouth-입술결절-1자', 'mouth-입술결절-함몰', 'mouth-위긴장도-있음', 'mouth-위긴장도-보통', 'mouth-위긴장도-없음', 'mouth-아래긴장도-있음', 'mouth-아래긴장도-보통', 'mouth-아래긴장도-없음', 'mouth-인중길이-짧아', 'mouth-인중길이-보통', 'mouth-인중길이-길어', 'mouth-인중너비-넓어', 'mouth-인중너비-보통', 'mouth-인중너비-좁아', 'mouth-팔자-깊은', 'mouth-팔자-보통', 'mouth-팔자-없음'],
        "2차 - 윤곽": ['silhouette-얼굴형-달걀형', 'silhouette-얼굴형-역삼각형', 'silhouette-얼굴형-긴', 'silhouette-얼굴형-동글', 'silhouette-얼굴형-사각형', 'silhouette-옆광대-크기-큰', 'silhouette-옆광대-크기-보통', 'silhouette-옆광대-크기-작은', 'silhouette-옆광대-높이-높은', 'silhouette-옆광대-높이-보통', 'silhouette-옆광대-높이-낮은', 'silhouette-옆광대-위치-밖', 'silhouette-옆광대-위치-보통', 'silhouette-옆광대-위치-안', 'silhouette-앞광대-크기-큰', 'silhouette-앞광대-크기-보통', 'silhouette-앞광대-크기-작은', 'silhouette-앞광대-높이-높은', 'silhouette-앞광대-높이-보통', 'silhouette-앞광대-높이-낮은', 'silhouette-턱-발달-발달', 'silhouette-턱-발달-보통', 'silhouette-턱-발달-무턱', 'silhouette-턱-형태-뾰족한', 'silhouette-턱-형태-보통', 'silhouette-턱-형태-각진', 'silhouette-턱-길이-긴', 'silhouette-턱-길이-보통', 'silhouette-턱-길이-짧은', 'silhouette-볼-살-살X', 'silhouette-볼-살-보통', 'silhouette-볼-살-살O', 'silhouette-볼-탄력-쳐진', 'silhouette-볼-탄력-보통', 'silhouette-볼-탄력-탄력'],
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
        st.metric("제안 경계값", f"{boundary_suggestion:.1f}")

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
                     annotation_text=f"제안 경계값: {boundary_suggestion:.1f}")

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("#### 📈 태그 그룹 통계")
        st.write(f"**평균:** {tag_mean:.2f}")
        st.write(f"**표준편차:** {tag_std:.2f}")
        st.write(f"**Q1:** {tag_q1:.2f}")
        st.write(f"**Q3:** {tag_q3:.2f}")

        st.write("#### 📈 전체 데이터 통계")
        st.write(f"**평균:** {all_mean:.2f}")
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
        st.write(f"{tag_q1:.1f} 이상")
        st.write(f"정확도: ~75%")

    with col2:
        st.write("**중간 기준 (평균)**")
        st.write(f"{tag_mean:.1f} 이상")
        st.write(f"정확도: ~50%")

    with col3:
        st.write("**관대한 기준 (Q3)**")
        st.write(f"{tag_q3:.1f} 이상")
        st.write(f"정확도: ~25%")

    # 상세 데이터
    with st.expander("📋 상세 데이터 보기"):
        detail_df = pd.DataFrame({
            '파일명': names_with_tag,
            '측정값': tag_data
        })
        detail_df = detail_df.sort_values('측정값', ascending=False)
        st.dataframe(detail_df, use_container_width=True)


def execute_level_comparison_analysis(landmarks_data, selected_feature, point1, point2, calc_type):
    """레벨별 비교 분석 실행"""
    st.write("### 🔄 비교 분석 실행 중...")

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

    # 상단 메트릭
    cols = st.columns(len(valid_levels))
    level_stats = {}

    for i, (level, data) in enumerate(valid_levels.items()):
        level_mean = np.mean(data)
        level_stats[level] = {
            'mean': level_mean,
            'std': np.std(data),
            'q1': np.percentile(data, 25),
            'q3': np.percentile(data, 75),
            'count': len(data)
        }

        with cols[i]:
            st.metric(
                level,
                f"평균 {level_mean:.1f}",
                f"{len(data)}개"
            )

    # 박스플롯 생성
    col1, col2 = st.columns([2, 1])

    with col1:
        # 데이터 준비
        plot_data = []
        for level, data in valid_levels.items():
            for val in data:
                plot_data.append({
                    'value': val,
                    'level': f'{level} ({len(data)}개)'
                })

        plot_df = pd.DataFrame(plot_data)

        fig = px.box(
            plot_df,
            x='level',
            y='value',
            title=f'{selected_feature} 레벨별 분포 비교',
            labels={'value': f'측정값 ({calc_type})', 'level': '레벨'}
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("#### 📈 레벨별 통계")
        for level, stats in level_stats.items():
            st.write(f"**{level}**")
            st.write(f"평균: {stats['mean']:.2f}")
            st.write(f"Q1-Q3: {stats['q1']:.1f} - {stats['q3']:.1f}")
            st.write("---")

    # 경계값 제안
    st.write("### 🎯 레벨별 경계값 제안")

    # 레벨을 평균값 순으로 정렬
    sorted_levels = sorted(level_stats.items(), key=lambda x: x[1]['mean'])

    if len(sorted_levels) >= 2:
        # 인접한 레벨 간 경계값 계산
        boundaries = []
        for i in range(len(sorted_levels) - 1):
            level1_name, level1_stats = sorted_levels[i]
            level2_name, level2_stats = sorted_levels[i + 1]

            # 중간값으로 경계 설정
            boundary = (level1_stats['q3'] + level2_stats['q1']) / 2
            boundaries.append({
                'lower_level': level1_name,
                'upper_level': level2_name,
                'boundary': boundary
            })

        for boundary_info in boundaries:
            st.write(f"**{boundary_info['lower_level']} vs {boundary_info['upper_level']}**")
            st.write(f"제안 경계값: {boundary_info['boundary']:.1f}")
            st.write(f"• {boundary_info['boundary']:.1f} 미만: {boundary_info['lower_level']}")
            st.write(f"• {boundary_info['boundary']:.1f} 이상: {boundary_info['upper_level']}")
            st.write("---")

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