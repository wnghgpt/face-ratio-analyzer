"""
데이터 선택 컴포넌트
태그 필터링, 날짜 범위, 수치 범위 등 다양한 필터링 옵션 제공
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any


def render_data_selector(db_manager, available_variables: List[str]) -> Dict[str, Any]:
    """데이터 선택 UI 렌더링"""

    st.subheader("📊 데이터 선택 및 필터링")

    filters = {}

    with st.expander("🏷️ 태그 필터", expanded=True):
        # 사용 가능한 태그 조회
        with db_manager.get_session() as session:
            from database.models import Tag
            available_tags = session.query(Tag.tag_name).distinct().all()
            tag_options = [tag[0] for tag in available_tags]

        if tag_options:
            col1, col2 = st.columns([3, 1])

            with col1:
                selected_tags = st.multiselect(
                    "포함할 태그 선택",
                    options=tag_options,
                    help="선택한 태그를 포함하는 데이터만 분석합니다"
                )

            with col2:
                tag_logic = st.radio(
                    "태그 조건",
                    ["OR", "AND"],
                    help="OR: 선택한 태그 중 하나라도 포함\nAND: 선택한 태그를 모두 포함"
                )

            if selected_tags:
                filters['tags'] = selected_tags
                filters['tag_logic'] = tag_logic
        else:
            st.info("사용 가능한 태그가 없습니다.")

    with st.expander("📅 날짜 범위 필터"):
        use_date_filter = st.checkbox("날짜 필터 사용")

        if use_date_filter:
            col1, col2 = st.columns(2)

            with col1:
                start_date = st.date_input(
                    "시작 날짜",
                    value=datetime.now() - timedelta(days=30),
                    help="이 날짜 이후의 데이터만 포함"
                )

            with col2:
                end_date = st.date_input(
                    "종료 날짜",
                    value=datetime.now(),
                    help="이 날짜 이전의 데이터만 포함"
                )

            if start_date <= end_date:
                filters['date_range'] = (start_date, end_date)
            else:
                st.error("시작 날짜가 종료 날짜보다 늦습니다.")

    with st.expander("🔢 수치 범위 필터"):
        # 동적으로 수치 변수들에 대한 범위 필터 생성
        numeric_vars = [var for var in available_variables if var.startswith('ratio_') or var == 'roll_angle']

        if numeric_vars:
            selected_var = st.selectbox(
                "필터링할 변수 선택",
                options=['없음'] + numeric_vars
            )

            if selected_var != '없음':
                # 해당 변수의 통계 정보 가져오기
                data_sample = db_manager.get_dataframe()
                if not data_sample.empty and selected_var in data_sample.columns:
                    var_data = data_sample[selected_var].dropna()

                    if len(var_data) > 0:
                        min_val = float(var_data.min())
                        max_val = float(var_data.max())
                        mean_val = float(var_data.mean())

                        st.write(f"**{selected_var}** 통계:")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("최솟값", f"{min_val:.3f}")
                        with col2:
                            st.metric("평균", f"{mean_val:.3f}")
                        with col3:
                            st.metric("최댓값", f"{max_val:.3f}")

                        # 범위 선택 슬라이더
                        range_values = st.slider(
                            f"{selected_var} 범위",
                            min_value=min_val,
                            max_value=max_val,
                            value=(min_val, max_val),
                            step=(max_val - min_val) / 100 if max_val != min_val else 0.01
                        )

                        if selected_var.startswith('ratio_2'):
                            filters['ratio_x_range'] = range_values
                        elif selected_var.startswith('ratio_3'):
                            filters['ratio_y_range'] = range_values
                        else:
                            filters[f'{selected_var}_range'] = range_values

    # 데이터 미리보기
    with st.expander("📋 데이터 미리보기", expanded=False):
        preview_data = db_manager.get_dataframe(filters if filters else None)

        if not preview_data.empty:
            st.write(f"**필터링된 데이터: {len(preview_data)}개 레코드**")

            # 기본 통계
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 레코드 수", len(preview_data))
            with col2:
                unique_tags = set()
                for tags in preview_data['tags_str'].dropna():
                    unique_tags.update([tag.strip() for tag in str(tags).split(',') if tag.strip()])
                st.metric("고유 태그 수", len(unique_tags))
            with col3:
                st.metric("수치 변수 수", len(preview_data.select_dtypes(include=['number']).columns))

            # 데이터 샘플 표시
            display_cols = ['name', 'tags_str'] + [col for col in preview_data.columns if col.startswith('ratio_')][:5]
            available_display_cols = [col for col in display_cols if col in preview_data.columns]

            if available_display_cols:
                st.dataframe(
                    preview_data[available_display_cols].head(10),
                    use_container_width=True
                )

            # 변수별 기본 통계
            if st.checkbox("변수별 상세 통계 보기"):
                numeric_data = preview_data.select_dtypes(include=['number'])
                if not numeric_data.empty:
                    st.write("**수치 변수 통계:**")
                    st.dataframe(numeric_data.describe(), use_container_width=True)
        else:
            st.warning("선택한 필터 조건에 맞는 데이터가 없습니다.")

    return filters


def render_data_summary(data: pd.DataFrame):
    """데이터 요약 정보 표시"""
    if data.empty:
        st.warning("표시할 데이터가 없습니다.")
        return

    st.subheader("📈 데이터 요약")

    # 기본 정보
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 레코드", len(data))

    with col2:
        numeric_cols = data.select_dtypes(include=['number']).columns
        st.metric("수치 변수", len(numeric_cols))

    with col3:
        # 태그 분석
        all_tags = []
        for tags_str in data['tags_str'].dropna():
            tags = [tag.strip() for tag in str(tags_str).split(',') if tag.strip()]
            all_tags.extend(tags)
        unique_tags = len(set(all_tags))
        st.metric("고유 태그", unique_tags)

    with col4:
        # 완전한 레코드 (모든 ratio 필드가 있는)
        ratio_cols = [col for col in data.columns if col.startswith('ratio_')]
        complete_records = len(data.dropna(subset=ratio_cols))
        st.metric("완전한 레코드", complete_records)

    # 가장 많이 사용된 태그 Top 10
    if all_tags:
        from collections import Counter
        tag_counts = Counter(all_tags)
        top_tags = tag_counts.most_common(10)

        if top_tags:
            st.write("**가장 많이 사용된 태그 Top 10:**")
            tag_df = pd.DataFrame(top_tags, columns=['태그', '사용 횟수'])
            st.dataframe(tag_df, use_container_width=True)


def get_filtered_data(db_manager, filters: Dict[str, Any]) -> pd.DataFrame:
    """필터를 적용하여 데이터 조회"""
    try:
        filtered_data = db_manager.get_dataframe(filters)
        return filtered_data
    except Exception as e:
        st.error(f"데이터 조회 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()