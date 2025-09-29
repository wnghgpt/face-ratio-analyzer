"""
Face Ratio Analyzer - Enhanced Version
다양한 비율 항목을 선택할 수 있는 얼굴 비율 분석 도구
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.db_manager import db_manager
from engines.ratio_parser import RatioParser
from engines.analysis_engine import AnalysisEngine
import json
import time


def main():
    """메인 애플리케이션"""
    st.set_page_config(
        page_title="Face Ratio Analyzer",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Face Ratio Analyzer - Enhanced")
    st.markdown("---")

    # 자동 새로고침 옵션
    with st.sidebar:
        st.markdown("---")
        auto_refresh = st.checkbox("🔄 자동 새로고침 (10초)", value=False)
        if auto_refresh:
            time.sleep(10)
            st.rerun()

        # 수동 새로고침 버튼
        if st.button("🔄 데이터 새로고침"):
            st.rerun()

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

    # 1. 비율 소스 선택
    st.sidebar.write("### 1. 분석할 비율 선택")

    # 사용 가능한 비율 옵션들 가져오기
    ratio_options = get_available_ratio_options(data)

    if not ratio_options:
        st.sidebar.error("사용 가능한 비율 데이터가 없습니다.")
        return

    # 비율 선택
    selected_ratio_name = st.sidebar.selectbox(
        "비율 종류",
        options=[opt['name'] for opt in ratio_options],
        format_func=lambda x: format_ratio_name(x)
    )

    # 선택된 비율의 정보 표시
    selected_ratio = next(opt for opt in ratio_options if opt['name'] == selected_ratio_name)

    with st.sidebar.expander("선택된 비율 정보"):
        st.write(f"**비율:** `{selected_ratio['sample_string']}`")
        st.write(f"**컴포넌트 수:** {selected_ratio['components']}")
        st.write(f"**사용 가능한 변수들:**")
        for var in selected_ratio['available_vars'][:5]:
            st.write(f"- {var}")

    # 2. 분석 도구 선택
    st.sidebar.write("### 2. 분석 도구 선택")
    analysis_type = st.sidebar.selectbox(
        "분석 방법",
        [
            "산점도 (Scatter Plot)",
            "히스토그램 (Histogram)",
            "박스플롯 (Box Plot)",
            "바이올린 플롯 (Violin Plot)",
            "PCA 분석",
            "클러스터링 (K-means)",
            "PCA + 클러스터링"
        ]
    )

    # 3. 변수 설정
    st.sidebar.write("### 3. 변수 설정")

    # 선택된 비율로 데이터 확장
    expanded_data = expand_data_with_ratios(data, selected_ratio_name)

    if expanded_data.empty:
        st.sidebar.error("선택된 비율로 확장된 데이터가 없습니다.")
        return

    available_vars = selected_ratio['available_vars']

    if analysis_type == "산점도 (Scatter Plot)":
        x_var, y_var = render_xy_selection(available_vars)
        if x_var and y_var:
            result = create_scatter_analysis(expanded_data, x_var, y_var)
            render_result(result, expanded_data, selected_ratio_name)

    elif analysis_type in ["히스토그램 (Histogram)", "박스플롯 (Box Plot)", "바이올린 플롯 (Violin Plot)"]:
        # 단일 변수 분석
        var_name = st.sidebar.selectbox(
            "분석할 변수",
            available_vars,
            help="분석할 단일 변수를 선택하세요"
        )
        if var_name:
            if analysis_type == "히스토그램 (Histogram)":
                result = create_histogram_analysis(expanded_data, var_name)
            elif analysis_type == "박스플롯 (Box Plot)":
                result = create_boxplot_analysis(expanded_data, var_name)
            elif analysis_type == "바이올린 플롯 (Violin Plot)":
                result = create_violin_analysis(expanded_data, var_name)

            render_result(result, expanded_data, selected_ratio_name)

    elif analysis_type == "PCA 분석":
        n_vars = st.sidebar.slider("사용할 변수 개수", 2, min(5, len(available_vars)), min(3, len(available_vars)))
        selected_vars = st.sidebar.multiselect(
            "분석할 변수들",
            available_vars,
            default=available_vars[:n_vars]
        )
        if len(selected_vars) >= 2:
            result = create_pca_analysis(expanded_data, selected_vars)
            render_result(result, expanded_data, selected_ratio_name)

    elif analysis_type == "클러스터링 (K-means)":
        n_vars = st.sidebar.slider("사용할 변수 개수", 2, min(5, len(available_vars)), min(3, len(available_vars)))
        n_clusters = st.sidebar.slider("클러스터 개수", 2, 8, 3)
        selected_vars = st.sidebar.multiselect(
            "분석할 변수들",
            available_vars,
            default=available_vars[:n_vars]
        )
        if len(selected_vars) >= 2:
            result = create_clustering_analysis(expanded_data, selected_vars, n_clusters)
            render_result(result, expanded_data, selected_ratio_name)

    elif analysis_type == "PCA + 클러스터링":
        n_vars = st.sidebar.slider("사용할 변수 개수", 2, min(5, len(available_vars)), min(3, len(available_vars)))
        n_clusters = st.sidebar.slider("클러스터 개수", 2, 8, 3)
        selected_vars = st.sidebar.multiselect(
            "분석할 변수들",
            available_vars,
            default=available_vars[:n_vars]
        )
        if len(selected_vars) >= 2:
            result = create_pca_clustering_analysis(expanded_data, selected_vars, n_clusters)
            render_result(result, expanded_data, selected_ratio_name)

    # 태그 필터링 옵션
    st.sidebar.markdown("---")
    st.sidebar.write("### 태그 필터링 (선택사항)")
    all_tags = get_all_tags(expanded_data)
    selected_tags = st.sidebar.multiselect("포함할 태그", all_tags)

    if selected_tags:
        filtered_data = filter_by_tags(expanded_data, selected_tags)
        st.sidebar.info(f"필터 결과: {len(filtered_data)}개 데이터")


def get_available_ratio_options(data):
    """사용 가능한 모든 비율 옵션들 반환"""
    parser = RatioParser()
    ratio_options = []

    for _, row in data.iterrows():
        # faceRatio 처리
        if pd.notna(row.get('face_ratio_raw')):
            face_ratio = row['face_ratio_raw']
            components = parser.parse_ratio_to_components(face_ratio)
            if components and 'faceRatio' not in [opt['name'] for opt in ratio_options]:
                ratio_options.append({
                    'name': 'faceRatio',
                    'sample_string': face_ratio,
                    'components': len(face_ratio.split(':')),
                    'available_vars': [k for k in components.keys() if k.startswith('ratio_')]
                })

        # ratios 객체 처리
        if pd.notna(row.get('ratios_detail')):
            try:
                # ratios_detail이 이미 dict인 경우와 문자열인 경우 모두 처리
                if isinstance(row['ratios_detail'], dict):
                    ratios_obj = row['ratios_detail']
                else:
                    ratios_obj = json.loads(row['ratios_detail'])

                extracted_ratios = extract_ratios_from_obj(ratios_obj, parser)

                for ratio_info in extracted_ratios:
                    # 중복 제거
                    if ratio_info['name'] not in [opt['name'] for opt in ratio_options]:
                        ratio_options.append(ratio_info)

            except (json.JSONDecodeError, TypeError):
                continue

    return ratio_options


def extract_ratios_from_obj(obj, parser, path=''):
    """ratios 객체에서 모든 비율 추출"""
    results = []

    def extract_recursive(current_obj, current_path=''):
        for key, value in current_obj.items():
            new_path = f'{current_path}_{key}' if current_path else key

            if isinstance(value, dict):
                if 'value' in value and isinstance(value['value'], str) and ':' in value['value']:
                    ratio_str = value['value']
                    components = parser.parse_ratio_to_components(ratio_str)
                    if components:
                        results.append({
                            'name': new_path,
                            'sample_string': ratio_str,
                            'components': len(ratio_str.split(':')),
                            'available_vars': [k for k in components.keys() if k.startswith('ratio_')]
                        })
                elif 'hasLeftRight' in value:
                    for side in ['left', 'right']:
                        if side in value and isinstance(value[side], str) and ':' in value[side]:
                            side_path = f'{new_path}_{side}'
                            ratio_str = value[side]
                            components = parser.parse_ratio_to_components(ratio_str)
                            if components:
                                results.append({
                                    'name': side_path,
                                    'sample_string': ratio_str,
                                    'components': len(ratio_str.split(':')),
                                    'available_vars': [k for k in components.keys() if k.startswith('ratio_')]
                                })
                else:
                    extract_recursive(value, new_path)
            elif isinstance(value, str) and ':' in value:
                components = parser.parse_ratio_to_components(value)
                if components:
                    results.append({
                        'name': new_path,
                        'sample_string': value,
                        'components': len(value.split(':')),
                        'available_vars': [k for k in components.keys() if k.startswith('ratio_')]
                    })

    extract_recursive(obj)
    return results


def format_ratio_name(name):
    """비율 이름을 사용자 친화적으로 포맷"""
    if name == 'faceRatio':
        return "🔹 기본 얼굴 비율"

    # 언더스코어를 공백으로 변경하고 이모지 추가
    formatted = name.replace('_', ' > ')

    if '눈' in formatted:
        return f"👁️ {formatted}"
    elif '코' in formatted:
        return f"👃 {formatted}"
    elif '입' in formatted:
        return f"👄 {formatted}"
    elif '눈썹' in formatted:
        return f"🤨 {formatted}"
    elif '전체비율' in formatted:
        return f"📏 {formatted}"
    else:
        return f"📊 {formatted}"


def expand_data_with_ratios(data, selected_ratio_name):
    """선택된 비율로 데이터 확장"""
    parser = RatioParser()
    expanded_data = data.copy()

    # 선택된 비율에 해당하는 데이터를 찾아서 파싱
    new_columns = {}

    for idx, row in data.iterrows():
        ratio_string = None

        if selected_ratio_name == 'faceRatio':
            ratio_string = row.get('face_ratio_raw')
        else:
            # ratios 객체에서 찾기
            if pd.notna(row.get('ratios_detail')):
                try:
                    # ratios_detail이 이미 dict인 경우와 문자열인 경우 모두 처리
                    if isinstance(row['ratios_detail'], dict):
                        ratios_obj = row['ratios_detail']
                    else:
                        ratios_obj = json.loads(row['ratios_detail'])
                    ratio_string = find_ratio_in_obj(ratios_obj, selected_ratio_name)
                except (json.JSONDecodeError, TypeError):
                    continue

        if ratio_string:
            components = parser.parse_ratio_to_components(ratio_string)
            for key, value in components.items():
                if key not in new_columns:
                    new_columns[key] = {}
                new_columns[key][idx] = value

    # 새 컬럼들을 데이터프레임에 추가
    for col_name, col_data in new_columns.items():
        expanded_data[col_name] = pd.Series(col_data)

    return expanded_data


def find_ratio_in_obj(obj, target_path):
    """ratios 객체에서 특정 경로의 비율 문자열 찾기"""
    def search_recursive(current_obj, current_path=''):
        for key, value in current_obj.items():
            new_path = f'{current_path}_{key}' if current_path else key

            if new_path == target_path:
                if isinstance(value, dict) and 'value' in value:
                    return value['value']
                elif isinstance(value, str) and ':' in value:
                    return value

            if isinstance(value, dict):
                if 'hasLeftRight' in value:
                    for side in ['left', 'right']:
                        side_path = f'{new_path}_{side}'
                        if side_path == target_path and side in value:
                            return value[side]
                else:
                    result = search_recursive(value, new_path)
                    if result:
                        return result
        return None

    return search_recursive(obj)


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


def render_xy_selection(available_vars):
    """X, Y축 변수 선택"""
    col1, col2 = st.sidebar.columns(2)

    with col1:
        x_var = st.selectbox("X축", ["선택"] + available_vars)

    with col2:
        y_var = st.selectbox("Y축", ["선택"] + available_vars)

    if x_var == "선택" or y_var == "선택":
        return None, None

    if x_var == y_var:
        st.sidebar.error("X축과 Y축이 같습니다")
        return None, None

    return x_var, y_var


def create_scatter_analysis(data, x_var, y_var):
    """산점도 분석"""
    # 유효한 데이터만 사용
    valid_data = data[[x_var, y_var, 'name', 'tags_str']].dropna()

    if len(valid_data) == 0:
        return {
            'type': '산점도',
            'figure': None,
            'stats': {'오류': '유효한 데이터가 없습니다'}
        }

    fig = px.scatter(
        valid_data,
        x=x_var,
        y=y_var,
        hover_data=['name', 'tags_str'],
        title=f"{y_var} vs {x_var}"
    )

    # 통계 계산
    correlation = valid_data[x_var].corr(valid_data[y_var])

    return {
        'type': '산점도',
        'figure': fig,
        'stats': {
            '상관계수': f"{correlation:.3f}",
            '데이터 수': len(valid_data),
            'X축 범위': f"{valid_data[x_var].min():.2f} ~ {valid_data[x_var].max():.2f}",
            'Y축 범위': f"{valid_data[y_var].min():.2f} ~ {valid_data[y_var].max():.2f}"
        }
    }


def create_pca_analysis(data, selected_vars):
    """PCA 분석"""
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    # 데이터 준비
    X = data[selected_vars].dropna()

    if len(X) < 2:
        return {
            'type': 'PCA',
            'figure': None,
            'stats': {'오류': '유효한 데이터가 부족합니다'}
        }

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

    if len(X) < n_clusters:
        return {
            'type': '클러스터링',
            'figure': None,
            'stats': {'오류': f'데이터가 클러스터 수({n_clusters})보다 적습니다'}
        }

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

    if len(X) < n_clusters:
        return {
            'type': 'PCA + 클러스터링',
            'figure': None,
            'stats': {'오류': f'데이터가 클러스터 수({n_clusters})보다 적습니다'}
        }

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


def create_histogram_analysis(data, var_name):
    """히스토그램 분석"""
    try:
        import plotly.express as px
        import numpy as np

        if var_name not in data.columns:
            return {
                'type': '히스토그램',
                'figure': None,
                'stats': {'오류': f'변수 {var_name}을 찾을 수 없습니다'}
            }

        values = data[var_name].dropna()
        if len(values) == 0:
            return {
                'type': '히스토그램',
                'figure': None,
                'stats': {'오류': '유효한 데이터가 없습니다'}
            }

        fig = px.histogram(
            x=values,
            nbins=20,
            title=f'{format_ratio_name(var_name)} 히스토그램',
            labels={'x': format_ratio_name(var_name), 'count': '빈도'}
        )

        fig.update_layout(
            showlegend=False,
            height=500
        )

        return {
            'type': '히스토그램',
            'figure': fig,
            'stats': {
                '평균': f"{values.mean():.3f}",
                '중앙값': f"{values.median():.3f}",
                '표준편차': f"{values.std():.3f}",
                '최솟값': f"{values.min():.3f}",
                '최댓값': f"{values.max():.3f}",
                '데이터 수': len(values)
            }
        }
    except Exception as e:
        return {
            'type': '히스토그램',
            'figure': None,
            'stats': {'오류': f'분석 중 오류 발생: {str(e)}'}
        }


def create_boxplot_analysis(data, var_name):
    """박스 플롯 분석"""
    try:
        import plotly.express as px
        import numpy as np

        if var_name not in data.columns:
            return {
                'type': '박스 플롯',
                'figure': None,
                'stats': {'오류': f'변수 {var_name}을 찾을 수 없습니다'}
            }

        values = data[var_name].dropna()
        if len(values) == 0:
            return {
                'type': '박스 플롯',
                'figure': None,
                'stats': {'오류': '유효한 데이터가 없습니다'}
            }

        # 태그별로 그룹화 (있는 경우)
        if 'tags_str' in data.columns and not data['tags_str'].isna().all():
            # 태그가 있는 데이터만 필터링
            tagged_data = data.dropna(subset=['tags_str', var_name])
            if len(tagged_data) > 0:
                fig = px.box(
                    tagged_data,
                    y=var_name,
                    x='tags_str',
                    title=f'{format_ratio_name(var_name)} 박스 플롯 (태그별)',
                    labels={var_name: format_ratio_name(var_name), 'tags_str': '태그'}
                )
            else:
                fig = px.box(
                    y=values,
                    title=f'{format_ratio_name(var_name)} 박스 플롯',
                    labels={'y': format_ratio_name(var_name)}
                )
        else:
            fig = px.box(
                y=values,
                title=f'{format_ratio_name(var_name)} 박스 플롯',
                labels={'y': format_ratio_name(var_name)}
            )

        fig.update_layout(height=500)

        # 이상치 검출
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = values[(values < lower_bound) | (values > upper_bound)]

        return {
            'type': '박스 플롯',
            'figure': fig,
            'stats': {
                '1사분위수 (Q1)': f"{Q1:.3f}",
                '중앙값 (Q2)': f"{values.median():.3f}",
                '3사분위수 (Q3)': f"{Q3:.3f}",
                '사분위범위 (IQR)': f"{IQR:.3f}",
                '이상치 개수': len(outliers),
                '데이터 수': len(values)
            }
        }
    except Exception as e:
        return {
            'type': '박스 플롯',
            'figure': None,
            'stats': {'오류': f'분석 중 오류 발생: {str(e)}'}
        }


def create_violin_analysis(data, var_name):
    """바이올린 플롯 분석"""
    try:
        import plotly.express as px
        import numpy as np

        if var_name not in data.columns:
            return {
                'type': '바이올린 플롯',
                'figure': None,
                'stats': {'오류': f'변수 {var_name}을 찾을 수 없습니다'}
            }

        values = data[var_name].dropna()
        if len(values) == 0:
            return {
                'type': '바이올린 플롯',
                'figure': None,
                'stats': {'오류': '유효한 데이터가 없습니다'}
            }

        # 태그별로 그룹화 (있는 경우)
        if 'tags_str' in data.columns and not data['tags_str'].isna().all():
            # 태그가 있는 데이터만 필터링
            tagged_data = data.dropna(subset=['tags_str', var_name])
            if len(tagged_data) > 0:
                fig = px.violin(
                    tagged_data,
                    y=var_name,
                    x='tags_str',
                    box=True,
                    title=f'{format_ratio_name(var_name)} 바이올린 플롯 (태그별)',
                    labels={var_name: format_ratio_name(var_name), 'tags_str': '태그'}
                )
            else:
                fig = px.violin(
                    y=values,
                    box=True,
                    title=f'{format_ratio_name(var_name)} 바이올린 플롯',
                    labels={'y': format_ratio_name(var_name)}
                )
        else:
            fig = px.violin(
                y=values,
                box=True,
                title=f'{format_ratio_name(var_name)} 바이올린 플롯',
                labels={'y': format_ratio_name(var_name)}
            )

        fig.update_layout(height=500)

        return {
            'type': '바이올린 플롯',
            'figure': fig,
            'stats': {
                '평균': f"{values.mean():.3f}",
                '중앙값': f"{values.median():.3f}",
                '표준편차': f"{values.std():.3f}",
                '왜도': f"{values.skew():.3f}",
                '첨도': f"{values.kurtosis():.3f}",
                '데이터 수': len(values)
            }
        }
    except Exception as e:
        return {
            'type': '바이올린 플롯',
            'figure': None,
            'stats': {'오류': f'분석 중 오류 발생: {str(e)}'}
        }


def render_result(result, data, selected_ratio_name):
    """결과 렌더링"""
    if result['figure'] is None:
        st.error(f"분석 실패: {result['stats'].get('오류', '알 수 없는 오류')}")
        return

    # 메인 그래프
    st.plotly_chart(result['figure'], use_container_width=True)

    # 통계 정보
    col1, col2 = st.columns([2, 1])

    with col1:
        st.write("### 📊 분석 결과")
        for key, value in result['stats'].items():
            st.write(f"**{key}:** {value}")

        st.write(f"**선택된 비율:** {format_ratio_name(selected_ratio_name)}")

    with col2:
        st.write("### 📋 데이터 샘플")
        display_cols = ['name', 'tags_str']
        if 'cluster' in data.columns:
            display_cols.append('cluster')

        sample_data = data[display_cols].dropna().head(5)
        if not sample_data.empty:
            st.dataframe(sample_data, use_container_width=True)


if __name__ == "__main__":
    main()