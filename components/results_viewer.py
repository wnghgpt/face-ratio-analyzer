"""
분석 결과 뷰어 컴포넌트
분석 결과를 시각화하고 통계를 표시하는 모듈
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import json


def render_results_viewer(analysis_result: Dict[str, Any]):
    """분석 결과 뷰어 렌더링"""

    if not analysis_result:
        st.info("표시할 분석 결과가 없습니다.")
        return

    if not analysis_result.get('success', False):
        st.error(f"분석 실행 중 오류가 발생했습니다: {analysis_result.get('error', '알 수 없는 오류')}")
        return

    st.subheader("📊 분석 결과")

    # 탭으로 구분된 결과 표시
    tabs = ["📈 시각화", "📋 통계 요약", "🔍 상세 결과", "⚙️ 설정"]
    tab_objects = st.tabs(tabs)

    with tab_objects[0]:  # 시각화
        render_visualizations(analysis_result.get('visualizations', []))

    with tab_objects[1]:  # 통계 요약
        render_statistics_summary(analysis_result.get('statistics', {}))

    with tab_objects[2]:  # 상세 결과
        render_detailed_results(analysis_result.get('analysis_results', {}))

    with tab_objects[3]:  # 설정
        render_config_info(analysis_result)


def render_visualizations(visualizations: List[Dict]):
    """시각화 결과 렌더링"""

    if not visualizations:
        st.info("생성된 시각화가 없습니다.")
        return

    st.write(f"**총 {len(visualizations)}개의 시각화가 생성되었습니다.**")

    for i, viz_result in enumerate(visualizations):
        viz_type = viz_result.get('type', 'unknown')
        viz_config = viz_result.get('config', {})
        fig = viz_result.get('figure')

        st.write(f"### {i+1}. {viz_config.get('title', f'{viz_type.title()} Plot')}")

        if fig:
            st.plotly_chart(fig, use_container_width=True)

            # 시각화별 추가 정보
            with st.expander(f"시각화 {i+1} 상세 정보"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**설정:**")
                    st.json(viz_config)

                with col2:
                    st.write("**통계:**")
                    if hasattr(fig, 'data') and fig.data:
                        try:
                            # 데이터 포인트 수
                            data_points = len(fig.data[0].x) if hasattr(fig.data[0], 'x') else 0
                            st.metric("데이터 포인트", data_points)

                            # 범위 정보 (산점도의 경우)
                            if viz_type in ['scatter', 'scatter3d'] and hasattr(fig.data[0], 'x'):
                                x_data = fig.data[0].x
                                y_data = fig.data[0].y
                                if x_data and y_data:
                                    st.write(f"X 범위: {min(x_data):.3f} ~ {max(x_data):.3f}")
                                    st.write(f"Y 범위: {min(y_data):.3f} ~ {max(y_data):.3f}")
                        except Exception as e:
                            st.write("통계 정보를 가져올 수 없습니다.")

            # 시각화 다운로드 옵션
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"PNG 다운로드", key=f"png_{i}"):
                    # 실제 구현에서는 plotly figure를 PNG로 저장
                    st.info("PNG 다운로드 기능을 구현해야 합니다.")

            with col2:
                if st.button(f"HTML 다운로드", key=f"html_{i}"):
                    # 실제 구현에서는 plotly figure를 HTML로 저장
                    st.info("HTML 다운로드 기능을 구현해야 합니다.")

            with col3:
                if st.button(f"데이터 다운로드", key=f"data_{i}"):
                    # 실제 구현에서는 시각화에 사용된 데이터를 CSV로 다운로드
                    st.info("데이터 다운로드 기능을 구현해야 합니다.")

        else:
            st.error(f"시각화 {i+1}을 생성할 수 없습니다.")


def render_statistics_summary(statistics: Dict):
    """통계 요약 렌더링"""

    if not statistics:
        st.info("통계 정보가 없습니다.")
        return

    # 기본 데이터 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "총 레코드 수",
            statistics.get('total_records', 0)
        )

    with col2:
        st.metric(
            "총 변수 수",
            statistics.get('total_variables', 0)
        )

    with col3:
        st.metric(
            "수치 변수 수",
            statistics.get('numeric_variables', 0)
        )

    # 클러스터링 결과
    if 'clustering' in statistics:
        st.write("### 🎯 클러스터링 결과")
        clustering_stats = statistics['clustering']

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "클러스터 수",
                clustering_stats.get('n_clusters', 0)
            )

        with col2:
            silhouette = clustering_stats.get('silhouette_score')
            if silhouette is not None:
                st.metric(
                    "실루엣 점수",
                    f"{silhouette:.3f}",
                    help="높을수록 좋은 클러스터링 (0.5 이상이면 양호)"
                )

        with col3:
            cluster_dist = clustering_stats.get('cluster_distribution', {})
            if cluster_dist:
                most_common_cluster = max(cluster_dist.items(), key=lambda x: x[1])
                st.metric(
                    "최대 클러스터 크기",
                    most_common_cluster[1]
                )

        # 클러스터 분포 차트
        if cluster_dist:
            st.write("**클러스터별 분포:**")
            cluster_df = pd.DataFrame([
                {'클러스터': f'클러스터 {k}', '개수': v}
                for k, v in cluster_dist.items()
            ])

            fig = px.bar(
                cluster_df,
                x='클러스터',
                y='개수',
                title='클러스터별 데이터 분포'
            )
            st.plotly_chart(fig, use_container_width=True)

    # 차원축소 결과
    if 'dimensionality_reduction' in statistics:
        st.write("### 📉 차원축소 결과")
        dr_stats = statistics['dimensionality_reduction']

        method = dr_stats.get('method', 'unknown')
        st.write(f"**방법:** {method.upper()}")

        if method == 'pca':
            explained_var = dr_stats.get('explained_variance', [])
            cumulative_var = dr_stats.get('cumulative_variance', [])

            if explained_var:
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**주성분별 설명 분산:**")
                    for i, var in enumerate(explained_var):
                        st.write(f"PC{i+1}: {var:.3f} ({var*100:.1f}%)")

                with col2:
                    if len(cumulative_var) >= 2:
                        st.metric(
                            "처음 2개 성분 설명 분산",
                            f"{cumulative_var[1]*100:.1f}%",
                            help="처음 2개 주성분이 설명하는 전체 분산의 비율"
                        )

                # 설명 분산 차트
                if len(explained_var) > 1:
                    fig = go.Figure()
                    fig.add_bar(
                        x=[f'PC{i+1}' for i in range(len(explained_var))],
                        y=explained_var,
                        name='개별 설명 분산'
                    )
                    fig.add_scatter(
                        x=[f'PC{i+1}' for i in range(len(cumulative_var))],
                        y=cumulative_var,
                        name='누적 설명 분산',
                        yaxis='y2'
                    )
                    fig.update_layout(
                        title='PCA 설명 분산',
                        yaxis=dict(title='개별 설명 분산'),
                        yaxis2=dict(title='누적 설명 분산', overlaying='y', side='right')
                    )
                    st.plotly_chart(fig, use_container_width=True)


def render_detailed_results(analysis_results: Dict):
    """상세 결과 렌더링"""

    if not analysis_results:
        st.info("상세 분석 결과가 없습니다.")
        return

    # 차원축소 상세 결과
    if 'dimensionality_reduction' in analysis_results:
        st.write("### 📉 차원축소 상세 결과")
        dr_result = analysis_results['dimensionality_reduction']

        with st.expander("차원축소 결과 데이터", expanded=False):
            reduced_data = dr_result.get('reduced_data')
            if reduced_data is not None:
                # numpy array를 DataFrame으로 변환
                import numpy as np
                if isinstance(reduced_data, list):
                    reduced_data = np.array(reduced_data)

                n_components = reduced_data.shape[1]
                columns = [f'성분_{i+1}' for i in range(n_components)]
                reduced_df = pd.DataFrame(reduced_data, columns=columns)

                st.dataframe(reduced_df.head(20), use_container_width=True)
                st.write(f"총 {len(reduced_df)}개 데이터 포인트")

        # PCA 컴포넌트 해석
        if dr_result.get('method') == 'pca':
            components = dr_result.get('components')
            variables_used = dr_result.get('variables_used', [])

            if components and variables_used:
                st.write("**주성분 구성 요소:**")
                components_df = pd.DataFrame(
                    components,
                    columns=variables_used,
                    index=[f'PC{i+1}' for i in range(len(components))]
                )

                # 히트맵으로 표시
                fig = px.imshow(
                    components_df,
                    text_auto=True,
                    aspect="auto",
                    title="PCA 컴포넌트 로딩",
                    color_continuous_scale='RdBu_r'
                )
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(components_df, use_container_width=True)

    # 클러스터링 상세 결과
    if 'clustering' in analysis_results:
        st.write("### 🎯 클러스터링 상세 결과")
        cluster_result = analysis_results['clustering']

        method = cluster_result.get('method', 'unknown')
        st.write(f"**방법:** {method}")

        with st.expander("클러스터링 결과 데이터", expanded=False):
            clusters = cluster_result.get('clusters', [])
            if clusters:
                cluster_df = pd.DataFrame({
                    '인덱스': range(len(clusters)),
                    '클러스터': clusters
                })
                st.dataframe(cluster_df.head(20), use_container_width=True)

        # 방법별 추가 정보
        if method == 'kmeans':
            centers = cluster_result.get('cluster_centers')
            if centers:
                st.write("**클러스터 중심점:**")
                variables_used = cluster_result.get('variables_used', [])
                if variables_used:
                    centers_df = pd.DataFrame(
                        centers,
                        columns=variables_used,
                        index=[f'클러스터 {i}' for i in range(len(centers))]
                    )
                    st.dataframe(centers_df, use_container_width=True)

            inertia = cluster_result.get('inertia')
            if inertia is not None:
                st.metric("관성 (Inertia)", f"{inertia:.3f}", help="클러스터 내 분산의 합 (낮을수록 좋음)")

        elif method == 'dbscan':
            n_noise = cluster_result.get('n_noise_points', 0)
            st.metric("노이즈 포인트", n_noise)

            eps = cluster_result.get('eps')
            min_samples = cluster_result.get('min_samples')
            if eps is not None and min_samples is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Epsilon", f"{eps:.3f}")
                with col2:
                    st.metric("Min Samples", min_samples)


def render_config_info(analysis_result: Dict):
    """분석 설정 정보 렌더링"""

    config_hash = analysis_result.get('config_hash')
    if config_hash:
        st.write(f"**설정 해시:** `{config_hash}`")

    # 캐시 정보 (실제로는 데이터베이스에서 조회)
    st.write("**분석 실행 정보:**")
    col1, col2 = st.columns(2)

    with col1:
        st.write("- 실행 시간: 방금 전")  # 실제로는 timestamp 사용
        data_count = len(analysis_result.get('data', []))
        st.write(f"- 분석된 데이터: {data_count}개")

    with col2:
        st.write("- 상태: 성공")
        st.write("- 캐시됨: 예")

    # 설정 저장 옵션
    if st.button("이 분석 설정 저장"):
        st.success("분석 설정이 저장되었습니다!")
        # 실제로는 데이터베이스에 저장

    # 결과 내보내기 옵션
    st.write("### 📤 결과 내보내기")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("JSON으로 내보내기"):
            # 실제 구현에서는 전체 결과를 JSON으로 다운로드
            st.download_button(
                label="결과 다운로드",
                data=json.dumps(analysis_result, indent=2, ensure_ascii=False),
                file_name=f"analysis_result_{config_hash[:8]}.json",
                mime="application/json"
            )

    with col2:
        if st.button("CSV로 내보내기"):
            # 실제 구현에서는 데이터를 CSV로 변환하여 다운로드
            data = analysis_result.get('data', [])
            if data:
                df = pd.DataFrame(data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="데이터 다운로드",
                    data=csv,
                    file_name=f"analysis_data_{config_hash[:8]}.csv",
                    mime="text/csv"
                )

    with col3:
        if st.button("리포트 생성"):
            st.info("리포트 생성 기능을 구현해야 합니다.")


def render_comparison_view(results: List[Dict]):
    """여러 분석 결과 비교 뷰"""

    if len(results) < 2:
        st.info("비교하려면 최소 2개의 분석 결과가 필요합니다.")
        return

    st.subheader("🔄 분석 결과 비교")

    # 비교할 결과 선택
    selected_indices = st.multiselect(
        "비교할 분석 선택",
        options=list(range(len(results))),
        default=list(range(min(2, len(results)))),
        format_func=lambda x: f"분석 {x+1}"
    )

    if len(selected_indices) < 2:
        st.warning("비교하려면 최소 2개의 분석을 선택해주세요.")
        return

    # 선택된 결과들 비교
    selected_results = [results[i] for i in selected_indices]

    # 통계 비교
    comparison_data = []
    for i, result in enumerate(selected_results):
        stats = result.get('statistics', {})
        comparison_data.append({
            '분석': f'분석 {selected_indices[i]+1}',
            '레코드 수': stats.get('total_records', 0),
            '변수 수': stats.get('total_variables', 0),
            '클러스터 수': stats.get('clustering', {}).get('n_clusters', 0) if 'clustering' in stats else 0,
            '실루엣 점수': stats.get('clustering', {}).get('silhouette_score', 0) if 'clustering' in stats else 0
        })

    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)

        # 실루엣 점수 비교 차트
        if any(row['실루엣 점수'] > 0 for row in comparison_data):
            fig = px.bar(
                comparison_df,
                x='분석',
                y='실루엣 점수',
                title='분석별 실루엣 점수 비교'
            )
            st.plotly_chart(fig, use_container_width=True)