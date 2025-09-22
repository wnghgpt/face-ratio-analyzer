"""
변수 선택 컴포넌트
분석에 사용할 변수들을 선택하고 조합을 검증하는 모듈
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple, Optional
from engines.ratio_parser import RatioParser


def render_variable_selector(data: pd.DataFrame, parser: RatioParser) -> Dict[str, any]:
    """변수 선택 UI 렌더링"""

    if data.empty:
        st.warning("분석할 데이터가 없습니다. 먼저 데이터를 선택해주세요.")
        return {}

    st.subheader("🎯 분석 변수 선택")

    # 사용 가능한 변수들 분석
    available_vars = [col for col in data.columns if col.startswith('ratio_') or col in ['roll_angle', 'tag_count']]

    if not available_vars:
        st.error("분석 가능한 변수가 없습니다.")
        return {}

    # 변수 추천 받기
    suggestions = parser.get_variable_suggestions(data)

    # 탭으로 구분된 선택 방식
    tab1, tab2, tab3 = st.tabs(["🎯 추천 조합", "🔧 수동 선택", "📊 변수 정보"])

    selection_result = {}

    with tab1:
        st.write("**분석 목적에 따른 추천 변수 조합:**")

        selected_analysis_type = st.selectbox(
            "분석 타입 선택",
            options=list(suggestions.keys()),
            format_func=lambda x: suggestions[x]['description']
        )

        if selected_analysis_type:
            analysis_info = suggestions[selected_analysis_type]

            col1, col2 = st.columns(2)

            with col1:
                st.write("**X축 추천 변수:**")
                x_options = analysis_info['x_axis']
                if x_options:
                    selected_x = st.selectbox(
                        "X축 변수",
                        options=x_options,
                        key="recommended_x"
                    )
                else:
                    st.warning("추천할 X축 변수가 없습니다.")
                    selected_x = None

            with col2:
                st.write("**Y축 추천 변수:**")
                y_options = analysis_info['y_axis']
                if y_options:
                    selected_y = st.selectbox(
                        "Y축 변수",
                        options=y_options,
                        key="recommended_y"
                    )
                else:
                    st.warning("추천할 Y축 변수가 없습니다.")
                    selected_y = None

            if selected_x and selected_y:
                # 변수 조합 검증
                validation = parser.validate_variable_combination(data, selected_x, selected_y)
                display_validation_result(validation, selected_x, selected_y)

                if validation['valid']:
                    selection_result = {
                        'x_variable': selected_x,
                        'y_variable': selected_y,
                        'analysis_type': selected_analysis_type,
                        'method': 'recommended'
                    }

    with tab2:
        st.write("**수동으로 변수 선택:**")

        col1, col2 = st.columns(2)

        with col1:
            manual_x = st.selectbox(
                "X축 변수 선택",
                options=['선택하세요'] + available_vars,
                key="manual_x"
            )

        with col2:
            manual_y = st.selectbox(
                "Y축 변수 선택",
                options=['선택하세요'] + available_vars,
                key="manual_y"
            )

        if manual_x != '선택하세요' and manual_y != '선택하세요':
            if manual_x == manual_y:
                st.error("X축과 Y축에 같은 변수를 선택할 수 없습니다.")
            else:
                # 변수 조합 검증
                validation = parser.validate_variable_combination(data, manual_x, manual_y)
                display_validation_result(validation, manual_x, manual_y)

                if validation['valid']:
                    selection_result = {
                        'x_variable': manual_x,
                        'y_variable': manual_y,
                        'method': 'manual'
                    }

        # 추가 변수 선택 (클러스터링, 색상 등)
        st.write("**추가 옵션:**")

        color_var = st.selectbox(
            "색상 구분 변수 (선택사항)",
            options=['없음'] + available_vars + ['cluster'] # cluster는 나중에 동적 생성
        )

        if color_var != '없음':
            if 'x_variable' in selection_result:
                selection_result['color_variable'] = color_var

    with tab3:
        st.write("**사용 가능한 변수들의 상세 정보:**")

        info_var = st.selectbox(
            "정보를 볼 변수 선택",
            options=available_vars
        )

        if info_var:
            var_info = parser.get_variable_info(data, info_var)
            display_variable_info(var_info)

    # 커스텀 변수 생성
    render_custom_variable_creator(data, parser)

    return selection_result


def display_validation_result(validation: Dict, x_var: str, y_var: str):
    """변수 조합 검증 결과 표시"""

    if validation['valid']:
        st.success(f"✅ {x_var} × {y_var} 조합이 유효합니다!")

        if 'statistics' in validation:
            stats = validation['statistics']

            # 통계 정보 표시
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "유효 데이터 수",
                    stats['common_valid_count']
                )

            with col2:
                corr = stats.get('correlation')
                if corr is not None:
                    st.metric(
                        "상관계수",
                        f"{corr:.3f}"
                    )

            with col3:
                if stats['common_valid_count'] > 0:
                    coverage = (stats['common_valid_count'] / stats['x_var_stats']['count']) * 100
                    st.metric(
                        "데이터 커버리지",
                        f"{coverage:.1f}%"
                    )

            # 각 변수의 상세 통계
            with st.expander("변수별 상세 통계"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**{x_var} 통계:**")
                    x_stats = stats['x_var_stats']
                    st.write(f"- 개수: {x_stats['count']}")
                    st.write(f"- 평균: {x_stats['mean']:.3f}")
                    st.write(f"- 표준편차: {x_stats['std']:.3f}")
                    st.write(f"- 범위: {x_stats['min']:.3f} ~ {x_stats['max']:.3f}")

                with col2:
                    st.write(f"**{y_var} 통계:**")
                    y_stats = stats['y_var_stats']
                    st.write(f"- 개수: {y_stats['count']}")
                    st.write(f"- 평균: {y_stats['mean']:.3f}")
                    st.write(f"- 표준편차: {y_stats['std']:.3f}")
                    st.write(f"- 범위: {y_stats['min']:.3f} ~ {y_stats['max']:.3f}")

    else:
        st.error("❌ 변수 조합이 유효하지 않습니다.")

    # 경고 메시지
    if validation['warnings']:
        for warning in validation['warnings']:
            st.warning(f"⚠️ {warning}")

    # 제안 메시지
    if validation['suggestions']:
        for suggestion in validation['suggestions']:
            st.info(f"💡 {suggestion}")


def display_variable_info(var_info: Dict):
    """변수 정보 표시"""

    if 'error' in var_info:
        st.error(var_info['error'])
        return

    st.write(f"**변수명:** {var_info['name']}")

    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("데이터 수", var_info['count'])

    with col2:
        st.metric("유효 비율", f"{var_info['valid_percentage']:.1f}%")

    with col3:
        st.metric("평균", f"{var_info['mean']:.3f}")

    with col4:
        st.metric("표준편차", f"{var_info['std']:.3f}")

    # 상세 통계
    col1, col2 = st.columns(2)

    with col1:
        st.write("**분포 정보:**")
        st.write(f"- 최솟값: {var_info['min']:.3f}")
        st.write(f"- 1사분위: {var_info['quartiles']['q1']:.3f}")
        st.write(f"- 중앙값: {var_info['median']:.3f}")
        st.write(f"- 3사분위: {var_info['quartiles']['q3']:.3f}")
        st.write(f"- 최댓값: {var_info['max']:.3f}")

    with col2:
        st.write("**데이터 품질:**")
        st.write(f"- 이상치 개수: {var_info['outlier_count']}")
        outlier_pct = (var_info['outlier_count'] / var_info['count']) * 100 if var_info['count'] > 0 else 0
        st.write(f"- 이상치 비율: {outlier_pct:.1f}%")

        quality_score = "우수" if outlier_pct < 5 else "보통" if outlier_pct < 15 else "주의"
        st.write(f"- 품질 평가: {quality_score}")


def render_custom_variable_creator(data: pd.DataFrame, parser: RatioParser):
    """커스텀 변수 생성 UI"""

    with st.expander("🧮 커스텀 변수 생성"):
        st.write("기존 변수들을 조합하여 새로운 변수를 만들 수 있습니다.")

        col1, col2 = st.columns([2, 1])

        with col1:
            var_name = st.text_input(
                "새 변수명",
                placeholder="예: ratio_harmony"
            )

            formula = st.text_input(
                "계산 공식",
                placeholder="예: (ratio_2 + ratio_3) / 2",
                help="사용 가능한 변수: " + ", ".join([col for col in data.columns if col.startswith('ratio_')])
            )

        with col2:
            st.write("**사용 가능한 함수:**")
            st.code("""
abs(x)    # 절댓값
sqrt(x)   # 제곱근
log(x)    # 자연로그
exp(x)    # 지수함수
""")

        if st.button("변수 생성"):
            if var_name and formula:
                try:
                    new_var = parser.create_custom_variable(data, var_name, formula)
                    st.success(f"✅ 변수 '{var_name}'가 성공적으로 생성되었습니다!")

                    # 미리보기
                    preview_data = pd.DataFrame({
                        '원본 인덱스': data.index[:5],
                        var_name: new_var.head()
                    })
                    st.write("**생성된 변수 미리보기:**")
                    st.dataframe(preview_data)

                except Exception as e:
                    st.error(f"❌ 변수 생성 실패: {e}")
            else:
                st.warning("변수명과 공식을 모두 입력해주세요.")


def get_analysis_variables(data: pd.DataFrame) -> Dict[str, List[str]]:
    """분석 타입별 추천 변수 목록 반환"""

    ratio_vars = [col for col in data.columns if col.startswith('ratio_')]
    calculated_vars = [col for col in ratio_vars if '_' in col and col.count('_') > 1]  # ratio_2_1 형태
    base_vars = [col for col in ratio_vars if col not in calculated_vars]  # ratio_1, ratio_2 형태

    return {
        "기본 비율": base_vars[:5],  # ratio_1, ratio_2, ratio_3 등
        "계산된 비율": calculated_vars[:5],  # ratio_2_1, ratio_3_1 등
        "모든 비율": ratio_vars,
        "추가 변수": ['roll_angle', 'tag_count']
    }