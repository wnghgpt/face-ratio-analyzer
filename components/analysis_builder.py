"""
분석 설정 빌더 컴포넌트
사용자가 원하는 분석 파이프라인을 구성할 수 있는 UI 제공
"""
import streamlit as st
import json
from typing import Dict, List, Any
from engines.analysis_engine import AnalysisEngine


def render_analysis_builder() -> Dict[str, Any]:
    """분석 설정 빌더 UI 렌더링"""

    st.subheader("🔧 분석 설정 구성")

    engine = AnalysisEngine()
    analysis_config = {}

    # 분석 템플릿 선택
    with st.expander("📋 분석 템플릿", expanded=True):
        templates = engine.get_analysis_templates()

        col1, col2 = st.columns([2, 1])

        with col1:
            selected_template = st.selectbox(
                "미리 정의된 분석 템플릿 선택",
                options=['없음'] + list(templates.keys()),
                format_func=lambda x: templates[x]['name'] if x != '없음' else x
            )

        with col2:
            if selected_template != '없음':
                if st.button("템플릿 적용"):
                    st.session_state['analysis_config'] = templates[selected_template]['config'].copy()
                    st.success(f"'{templates[selected_template]['name']}' 템플릿이 적용되었습니다!")
                    st.rerun()

        if selected_template != '없음':
            template_info = templates[selected_template]
            st.write(f"**설명:** {template_info['description']}")

            with st.expander("템플릿 설정 미리보기"):
                st.json(template_info['config'])

    # 세션 상태에서 현재 설정 가져오기
    if 'analysis_config' not in st.session_state:
        st.session_state['analysis_config'] = {}

    current_config = st.session_state['analysis_config']

    # 1. 전처리 설정
    with st.expander("🔄 데이터 전처리 설정"):
        preprocessing_config = render_preprocessing_config(current_config.get('preprocessing', {}))
        if preprocessing_config:
            current_config['preprocessing'] = preprocessing_config

    # 2. 차원축소 설정
    with st.expander("📉 차원축소 설정"):
        use_dr = st.checkbox(
            "차원축소 사용",
            value='dimensionality_reduction' in current_config
        )

        if use_dr:
            dr_config = render_dimensionality_reduction_config(
                current_config.get('dimensionality_reduction', {})
            )
            if dr_config:
                current_config['dimensionality_reduction'] = dr_config
        else:
            current_config.pop('dimensionality_reduction', None)

    # 3. 클러스터링 설정
    with st.expander("🎯 클러스터링 설정"):
        use_clustering = st.checkbox(
            "클러스터링 사용",
            value='clustering' in current_config
        )

        if use_clustering:
            clustering_config = render_clustering_config(
                current_config.get('clustering', {})
            )
            if clustering_config:
                current_config['clustering'] = clustering_config
        else:
            current_config.pop('clustering', None)

    # 4. 시각화 설정
    with st.expander("📊 시각화 설정"):
        viz_configs = render_visualization_config(
            current_config.get('visualizations', [])
        )
        if viz_configs:
            current_config['visualizations'] = viz_configs

    # 설정 저장 및 불러오기
    with st.expander("💾 설정 관리"):
        render_config_management(current_config)

    # 현재 설정 미리보기
    with st.expander("👀 현재 설정 미리보기"):
        if current_config:
            st.json(current_config)
        else:
            st.info("설정이 없습니다.")

    # 세션 상태 업데이트
    st.session_state['analysis_config'] = current_config

    return current_config


def render_preprocessing_config(current_config: Dict) -> Dict:
    """전처리 설정 UI"""

    col1, col2 = st.columns(2)

    with col1:
        handle_missing = st.checkbox(
            "결측값 처리",
            value=current_config.get('handle_missing', True),
            help="수치 변수의 결측값을 평균으로 대체합니다"
        )

        scaling = st.selectbox(
            "데이터 스케일링",
            options=['none', 'standard', 'minmax'],
            index=['none', 'standard', 'minmax'].index(current_config.get('scaling', 'none')),
            help="standard: 평균=0, 표준편차=1\nminmax: 최솟값=0, 최댓값=1"
        )

    with col2:
        remove_outliers = st.checkbox(
            "이상치 제거",
            value=current_config.get('remove_outliers', False),
            help="통계적 방법으로 이상치를 제거합니다"
        )

        if remove_outliers:
            outlier_method = st.selectbox(
                "이상치 제거 방법",
                options=['iqr', 'zscore'],
                index=['iqr', 'zscore'].index(current_config.get('outlier_method', 'iqr')),
                help="IQR: 사분위범위 기반\nZ-score: 표준편차 기반"
            )
        else:
            outlier_method = 'iqr'

    return {
        'handle_missing': handle_missing,
        'scaling': scaling,
        'remove_outliers': remove_outliers,
        'outlier_method': outlier_method
    }


def render_dimensionality_reduction_config(current_config: Dict) -> Dict:
    """차원축소 설정 UI"""

    method = st.selectbox(
        "차원축소 방법",
        options=['pca', 'tsne', 'umap'],
        index=['pca', 'tsne', 'umap'].index(current_config.get('method', 'pca')),
        help="PCA: 주성분분석\nt-SNE: t-분포 확률적 임베딩\nUMAP: 균등 매니폴드 근사"
    )

    col1, col2 = st.columns(2)

    with col1:
        n_components = st.number_input(
            "출력 차원 수",
            min_value=2,
            max_value=10,
            value=current_config.get('n_components', 2),
            help="줄일 차원의 수 (보통 2D 또는 3D)"
        )

    config = {
        'method': method,
        'n_components': n_components
    }

    # 방법별 추가 파라미터
    if method == 'tsne':
        with col2:
            perplexity = st.number_input(
                "Perplexity",
                min_value=5,
                max_value=50,
                value=current_config.get('perplexity', 30),
                help="이웃점 수를 결정하는 파라미터"
            )
            config['perplexity'] = perplexity

        learning_rate = st.number_input(
            "Learning Rate",
            min_value=10,
            max_value=1000,
            value=current_config.get('learning_rate', 200),
            help="학습률"
        )
        config['learning_rate'] = learning_rate

    elif method == 'umap':
        with col2:
            n_neighbors = st.number_input(
                "N Neighbors",
                min_value=5,
                max_value=100,
                value=current_config.get('n_neighbors', 15),
                help="이웃점 수"
            )
            config['n_neighbors'] = n_neighbors

        min_dist = st.slider(
            "Min Distance",
            min_value=0.0,
            max_value=1.0,
            value=current_config.get('min_dist', 0.1),
            step=0.05,
            help="임베딩에서 점들 간 최소 거리"
        )
        config['min_dist'] = min_dist

    return config


def render_clustering_config(current_config: Dict) -> Dict:
    """클러스터링 설정 UI"""

    method = st.selectbox(
        "클러스터링 방법",
        options=['kmeans', 'dbscan', 'hierarchical'],
        index=['kmeans', 'dbscan', 'hierarchical'].index(current_config.get('method', 'kmeans')),
        help="K-means: 중심점 기반\nDBSCAN: 밀도 기반\nHierarchical: 계층적"
    )

    config = {'method': method}

    if method == 'kmeans':
        n_clusters = st.number_input(
            "클러스터 수",
            min_value=2,
            max_value=20,
            value=current_config.get('n_clusters', 3),
            help="생성할 클러스터의 개수"
        )
        config['n_clusters'] = n_clusters

    elif method == 'dbscan':
        col1, col2 = st.columns(2)

        with col1:
            eps = st.number_input(
                "Epsilon",
                min_value=0.1,
                max_value=5.0,
                value=current_config.get('eps', 0.5),
                step=0.1,
                help="이웃 영역의 반지름"
            )

        with col2:
            min_samples = st.number_input(
                "Min Samples",
                min_value=2,
                max_value=20,
                value=current_config.get('min_samples', 5),
                help="코어 포인트가 되기 위한 최소 점의 수"
            )

        config.update({
            'eps': eps,
            'min_samples': min_samples
        })

    elif method == 'hierarchical':
        col1, col2 = st.columns(2)

        with col1:
            n_clusters = st.number_input(
                "클러스터 수",
                min_value=2,
                max_value=20,
                value=current_config.get('n_clusters', 3)
            )

        with col2:
            linkage = st.selectbox(
                "Linkage",
                options=['ward', 'complete', 'average', 'single'],
                index=['ward', 'complete', 'average', 'single'].index(current_config.get('linkage', 'ward')),
                help="클러스터 간 거리 계산 방법"
            )

        config.update({
            'n_clusters': n_clusters,
            'linkage': linkage
        })

    return config


def render_visualization_config(current_configs: List[Dict]) -> List[Dict]:
    """시각화 설정 UI"""

    st.write("**시각화 추가:**")

    # 기존 시각화들 표시
    if current_configs:
        for i, viz_config in enumerate(current_configs):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"📊 {viz_config.get('type', 'unknown')} - {viz_config.get('title', 'Untitled')}")

                with col2:
                    if st.button("편집", key=f"edit_viz_{i}"):
                        st.session_state[f'editing_viz_{i}'] = True

                with col3:
                    if st.button("삭제", key=f"delete_viz_{i}"):
                        current_configs.pop(i)
                        st.rerun()

    # 새 시각화 추가
    with st.expander("➕ 새 시각화 추가"):
        viz_type = st.selectbox(
            "시각화 타입",
            options=['scatter', 'scatter3d', 'heatmap', 'histogram', 'box', 'violin'],
            help="scatter: 산점도\nscatter3d: 3D 산점도\nheatmap: 히트맵\nhistogram: 히스토그램\nbox: 박스플롯\nviolin: 바이올린 플롯"
        )

        title = st.text_input("시각화 제목", value=f"{viz_type.title()} Plot")

        # 시각화 타입별 추가 설정
        viz_config = {'type': viz_type, 'title': title}

        if viz_type in ['scatter', 'scatter3d']:
            col1, col2 = st.columns(2)

            with col1:
                use_dr = st.checkbox("차원축소 결과 사용", help="PCA, t-SNE 등의 결과를 X, Y축으로 사용")
                viz_config['use_dimensionality_reduction'] = use_dr

            with col2:
                use_clustering = st.checkbox("클러스터링 결과 사용", help="클러스터링 결과를 색상으로 표시")
                viz_config['use_clustering'] = use_clustering

            if not use_dr:
                x_axis = st.text_input("X축 변수", placeholder="ratio_2")
                y_axis = st.text_input("Y축 변수", placeholder="ratio_3")
                viz_config.update({'x_axis': x_axis, 'y_axis': y_axis})

                if viz_type == 'scatter3d':
                    z_axis = st.text_input("Z축 변수", placeholder="ratio_4")
                    viz_config['z_axis'] = z_axis

        elif viz_type in ['histogram', 'box', 'violin']:
            variable = st.text_input("분석할 변수", placeholder="ratio_2")
            viz_config['variable'] = variable

            if viz_type in ['box', 'violin']:
                group_by = st.text_input("그룹화 변수 (선택사항)", placeholder="cluster")
                if group_by:
                    viz_config['group_by'] = group_by

        elif viz_type == 'heatmap':
            variables = st.text_area(
                "변수 목록 (콤마 구분)",
                placeholder="ratio_1, ratio_2, ratio_3",
                help="상관관계를 분석할 변수들을 콤마로 구분하여 입력"
            )
            if variables:
                viz_config['variables'] = [v.strip() for v in variables.split(',')]

        if st.button("시각화 추가"):
            current_configs.append(viz_config)
            st.success("시각화가 추가되었습니다!")
            st.rerun()

    return current_configs


def render_config_management(current_config: Dict):
    """설정 저장 및 불러오기 UI"""

    col1, col2 = st.columns(2)

    with col1:
        st.write("**설정 저장:**")
        config_name = st.text_input("설정 이름", placeholder="내 분석 설정")
        config_description = st.text_area("설명", placeholder="이 설정에 대한 설명...")
        config_tags = st.text_input("태그 (콤마 구분)", placeholder="pca, clustering, basic")

        if st.button("설정 저장"):
            if config_name and current_config:
                # 여기서 실제로는 database에 저장해야 함
                st.success(f"설정 '{config_name}'이 저장되었습니다!")
            else:
                st.warning("설정 이름과 분석 설정이 필요합니다.")

    with col2:
        st.write("**저장된 설정 불러오기:**")
        # 여기서 실제로는 database에서 불러와야 함
        saved_configs = ["기본 PCA 분석", "클러스터링 분석", "고급 분석"]

        selected_saved_config = st.selectbox(
            "불러올 설정 선택",
            options=['없음'] + saved_configs
        )

        if st.button("설정 불러오기"):
            if selected_saved_config != '없음':
                st.success(f"설정 '{selected_saved_config}'이 불러와졌습니다!")
                # 실제로는 database에서 설정을 불러와서 session_state에 저장
            else:
                st.warning("불러올 설정을 선택해주세요.")


def validate_analysis_config(config: Dict) -> Dict[str, Any]:
    """분석 설정 유효성 검증"""

    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    # 필수 설정 확인
    if not config:
        validation_result['valid'] = False
        validation_result['errors'].append("분석 설정이 비어있습니다.")
        return validation_result

    # 시각화 설정 확인
    if 'visualizations' in config:
        for i, viz_config in enumerate(config['visualizations']):
            if viz_config.get('type') in ['scatter', 'scatter3d']:
                if not viz_config.get('use_dimensionality_reduction'):
                    if not viz_config.get('x_axis') or not viz_config.get('y_axis'):
                        validation_result['errors'].append(
                            f"시각화 {i+1}: X축과 Y축 변수가 필요합니다."
                        )

    # 차원축소 + 클러스터링 조합 경고
    if 'dimensionality_reduction' in config and 'clustering' in config:
        validation_result['warnings'].append(
            "차원축소와 클러스터링을 함께 사용할 때는 차원축소 결과에 클러스터링이 적용됩니다."
        )

    if validation_result['errors']:
        validation_result['valid'] = False

    return validation_result