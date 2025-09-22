"""
Face Ratio Analyzer - Simple Version
간단하고 직관적인 얼굴 비율 분석 도구
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.db_manager import db_manager
from engines.ratio_parser import RatioParser
from engines.analysis_engine import AnalysisEngine


def main():
    """메인 애플리케이션"""
    st.set_page_config(
        page_title="Face Ratio Analyzer",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Face Ratio Analyzer")
    st.markdown("---")

    # 데이터 확인
    data = db_manager.get_dataframe()

    if data.empty:
        st.warning("⚠️ 분석할 데이터가 없습니다.")
        st.info("💡 먼저 JSON 파일들을 데이터베이스에 가져와주세요.")

        # 간단한 데이터 가져오기
        with st.expander("📥 데이터 가져오기"):
            render_simple_import()
        return

    # 메인 분석 인터페이스
    st.sidebar.header("⚙️ 분석 설정")

    # 데이터 요약
    st.sidebar.write("**📊 데이터 현황**")
    st.sidebar.metric("총 데이터", len(data))
    st.sidebar.metric("고유 태그", len(get_all_tags(data)))

    # 1. 분석 도구 선택
    st.sidebar.write("### 1. 분석 도구 선택")
    analysis_type = st.sidebar.selectbox(
        "분석 방법",
        [
            "산점도 (Scatter Plot)",
            "PCA 분석",
            "클러스터링 (K-means)",
            "PCA + 클러스터링"
        ]
    )

    # 2. 변수 설정
    st.sidebar.write("### 2. 변수 설정")
    ratio_vars = get_ratio_variables(data)

    if analysis_type == "산점도 (Scatter Plot)":
        x_var, y_var = render_xy_selection(ratio_vars)
        if x_var and y_var:
            result = create_scatter_analysis(data, x_var, y_var)
            render_result(result, data)

    elif analysis_type == "PCA 분석":
        n_vars = st.sidebar.slider("사용할 변수 개수", 2, min(5, len(ratio_vars)), 3)
        selected_vars = st.sidebar.multiselect(
            "분석할 변수들",
            ratio_vars,
            default=ratio_vars[:n_vars]
        )
        if len(selected_vars) >= 2:
            result = create_pca_analysis(data, selected_vars)
            render_result(result, data)

    elif analysis_type == "클러스터링 (K-means)":
        n_vars = st.sidebar.slider("사용할 변수 개수", 2, min(5, len(ratio_vars)), 3)
        n_clusters = st.sidebar.slider("클러스터 개수", 2, 8, 3)
        selected_vars = st.sidebar.multiselect(
            "분석할 변수들",
            ratio_vars,
            default=ratio_vars[:n_vars]
        )
        if len(selected_vars) >= 2:
            result = create_clustering_analysis(data, selected_vars, n_clusters)
            render_result(result, data)

    elif analysis_type == "PCA + 클러스터링":
        n_vars = st.sidebar.slider("사용할 변수 개수", 2, min(5, len(ratio_vars)), 3)
        n_clusters = st.sidebar.slider("클러스터 개수", 2, 8, 3)
        selected_vars = st.sidebar.multiselect(
            "분석할 변수들",
            ratio_vars,
            default=ratio_vars[:n_vars]
        )
        if len(selected_vars) >= 2:
            result = create_pca_clustering_analysis(data, selected_vars, n_clusters)
            render_result(result, data)

    # 태그 필터링 옵션
    st.sidebar.markdown("---")
    st.sidebar.write("### 태그 필터링 (선택사항)")
    all_tags = get_all_tags(data)
    selected_tags = st.sidebar.multiselect("포함할 태그", all_tags)

    if selected_tags:
        filtered_data = filter_by_tags(data, selected_tags)
        st.sidebar.info(f"필터 결과: {len(filtered_data)}개 데이터")


def render_simple_import():
    """간단한 데이터 가져오기"""
    import os
    import json
    from pathlib import Path

    json_folder = st.text_input("JSON 폴더 경로", "json_files/")

    if st.button("데이터 가져오기"):
        if os.path.exists(json_folder):
            json_files = list(Path(json_folder).glob("*.json"))

            if json_files:
                json_data_list = []
                for file_path in json_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            data['_filename'] = file_path.name
                            json_data_list.append(data)
                    except Exception as e:
                        st.warning(f"파일 {file_path.name} 오류: {e}")

                if json_data_list:
                    db_manager.import_json_data(json_data_list)
                    st.success(f"✅ {len(json_data_list)}개 파일 가져오기 완료!")
                    st.rerun()
            else:
                st.error("JSON 파일이 없습니다.")
        else:
            st.error("폴더가 존재하지 않습니다.")


def get_ratio_variables(data):
    """비율 변수 목록 반환"""
    ratio_cols = [col for col in data.columns if col.startswith('ratio_') and col != 'ratio_sum']
    return ratio_cols[:6]  # 최대 6개만


def get_all_tags(data):
    """모든 고유 태그 반환"""
    all_tags = set()
    for tags_str in data['tags_str'].dropna():
        if tags_str:
            tags = [tag.strip() for tag in str(tags_str).split(',')]
            all_tags.update(tags)
    return sorted(list(all_tags))


def filter_by_tags(data, selected_tags):
    """태그로 데이터 필터링"""
    mask = pd.Series([False] * len(data))

    for idx, tags_str in data['tags_str'].items():
        if pd.notna(tags_str):
            tags = [tag.strip() for tag in str(tags_str).split(',')]
            if any(tag in tags for tag in selected_tags):
                mask[idx] = True

    return data[mask]


def render_xy_selection(ratio_vars):
    """X, Y축 변수 선택"""
    col1, col2 = st.sidebar.columns(2)

    with col1:
        x_var = st.selectbox("X축", ["선택"] + ratio_vars)

    with col2:
        y_var = st.selectbox("Y축", ["선택"] + ratio_vars)

    if x_var == "선택" or y_var == "선택":
        return None, None

    if x_var == y_var:
        st.sidebar.error("X축과 Y축이 같습니다")
        return None, None

    return x_var, y_var


def create_scatter_analysis(data, x_var, y_var):
    """산점도 분석"""
    fig = px.scatter(
        data,
        x=x_var,
        y=y_var,
        hover_data=['name', 'tags_str'],
        title=f"{y_var} vs {x_var}"
    )

    # 통계 계산
    correlation = data[x_var].corr(data[y_var])

    return {
        'type': '산점도',
        'figure': fig,
        'stats': {
            '상관계수': f"{correlation:.3f}",
            '데이터 수': len(data),
            'X축 범위': f"{data[x_var].min():.2f} ~ {data[x_var].max():.2f}",
            'Y축 범위': f"{data[y_var].min():.2f} ~ {data[y_var].max():.2f}"
        }
    }


def create_pca_analysis(data, selected_vars):
    """PCA 분석"""
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    # 데이터 준비
    X = data[selected_vars].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # PCA 수행
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    # 결과 데이터프레임 생성
    pca_df = data.loc[X.index].copy()
    pca_df['PC1'] = X_pca[:, 0]
    pca_df['PC2'] = X_pca[:, 1]

    # 시각화
    fig = px.scatter(
        pca_df,
        x='PC1',
        y='PC2',
        hover_data=['name', 'tags_str'],
        title='PCA 분석 결과'
    )

    return {
        'type': 'PCA',
        'figure': fig,
        'stats': {
            'PC1 설명 분산': f"{pca.explained_variance_ratio_[0]:.1%}",
            'PC2 설명 분산': f"{pca.explained_variance_ratio_[1]:.1%}",
            '총 설명 분산': f"{pca.explained_variance_ratio_.sum():.1%}",
            '사용 변수': ', '.join(selected_vars)
        }
    }


def create_clustering_analysis(data, selected_vars, n_clusters):
    """클러스터링 분석"""
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    # 데이터 준비
    X = data[selected_vars].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # K-means 수행
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)

    # 첫 2개 변수로 시각화
    cluster_df = data.loc[X.index].copy()
    cluster_df['cluster'] = clusters

    fig = px.scatter(
        cluster_df,
        x=selected_vars[0],
        y=selected_vars[1],
        color='cluster',
        hover_data=['name', 'tags_str'],
        title=f'클러스터링 결과 (K={n_clusters})'
    )

    # 클러스터별 통계
    cluster_stats = {}
    for i in range(n_clusters):
        mask = clusters == i
        cluster_stats[f'클러스터 {i}'] = len(X[mask])

    return {
        'type': '클러스터링',
        'figure': fig,
        'stats': {
            '클러스터 수': n_clusters,
            '관성': f"{kmeans.inertia_:.2f}",
            **cluster_stats,
            '사용 변수': ', '.join(selected_vars)
        }
    }


def create_pca_clustering_analysis(data, selected_vars, n_clusters):
    """PCA + 클러스터링 분석"""
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    # 데이터 준비
    X = data[selected_vars].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # PCA 수행
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    # 클러스터링 수행 (PCA 결과에 대해)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X_pca)

    # 결과 데이터프레임 생성
    result_df = data.loc[X.index].copy()
    result_df['PC1'] = X_pca[:, 0]
    result_df['PC2'] = X_pca[:, 1]
    result_df['cluster'] = clusters

    # 시각화
    fig = px.scatter(
        result_df,
        x='PC1',
        y='PC2',
        color='cluster',
        hover_data=['name', 'tags_str'],
        title=f'PCA + 클러스터링 결과 (K={n_clusters})'
    )

    # 클러스터별 통계
    cluster_stats = {}
    for i in range(n_clusters):
        mask = clusters == i
        cluster_stats[f'클러스터 {i}'] = len(X_pca[mask])

    return {
        'type': 'PCA + 클러스터링',
        'figure': fig,
        'stats': {
            'PC1 설명 분산': f"{pca.explained_variance_ratio_[0]:.1%}",
            'PC2 설명 분산': f"{pca.explained_variance_ratio_[1]:.1%}",
            '클러스터 수': n_clusters,
            **cluster_stats,
            '사용 변수': ', '.join(selected_vars)
        }
    }


def render_result(result, data):
    """결과 렌더링"""
    # 메인 그래프
    st.plotly_chart(result['figure'], use_container_width=True)

    # 통계 정보
    col1, col2 = st.columns([2, 1])

    with col1:
        st.write("### 📊 분석 결과")
        for key, value in result['stats'].items():
            st.write(f"**{key}:** {value}")

    with col2:
        st.write("### 📋 데이터 샘플")
        display_cols = ['name', 'tags_str']
        if 'cluster' in data.columns:
            display_cols.append('cluster')
        st.dataframe(data[display_cols].head(5), use_container_width=True)


if __name__ == "__main__":
    main()