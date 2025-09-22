"""
동적 분석 엔진
사용자 설정에 따라 다양한 분석을 수행하는 모듈
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import silhouette_score
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import json


class AnalysisEngine:
    def __init__(self):
        self.preprocessors = {
            'standard': StandardScaler,
            'minmax': MinMaxScaler,
            'none': lambda: None
        }

        self.dimensionality_reducers = {
            'pca': self._apply_pca,
            'tsne': self._apply_tsne,
            'umap': self._apply_umap  # UMAP은 별도 패키지 필요
        }

        self.clusterers = {
            'kmeans': self._apply_kmeans,
            'dbscan': self._apply_dbscan,
            'hierarchical': self._apply_hierarchical
        }

        self.visualizers = {
            'scatter': self._create_scatter_plot,
            'scatter3d': self._create_3d_scatter_plot,
            'heatmap': self._create_heatmap,
            'histogram': self._create_histogram,
            'box': self._create_box_plot,
            'violin': self._create_violin_plot
        }

    def execute_analysis(self, data: pd.DataFrame, config: Dict) -> Dict:
        """분석 실행 메인 함수"""
        try:
            # 1. 데이터 전처리
            processed_data = self._preprocess_data(data, config.get('preprocessing', {}))

            # 2. 분석 실행
            analysis_results = {}

            # 차원축소
            if 'dimensionality_reduction' in config:
                dr_config = config['dimensionality_reduction']
                dr_result = self._apply_dimensionality_reduction(processed_data, dr_config)
                analysis_results['dimensionality_reduction'] = dr_result

            # 클러스터링
            if 'clustering' in config:
                cluster_config = config['clustering']
                cluster_result = self._apply_clustering(processed_data, cluster_config)
                analysis_results['clustering'] = cluster_result

            # 3. 시각화
            visualizations = []
            if 'visualizations' in config:
                for viz_config in config['visualizations']:
                    viz_result = self._create_visualization(processed_data, viz_config, analysis_results)
                    visualizations.append(viz_result)

            # 4. 통계 계산
            statistics = self._calculate_statistics(processed_data, analysis_results)

            return {
                'success': True,
                'data': processed_data.to_dict('records'),
                'analysis_results': analysis_results,
                'visualizations': visualizations,
                'statistics': statistics,
                'config_hash': self._generate_config_hash(config)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'config_hash': self._generate_config_hash(config)
            }

    def _preprocess_data(self, data: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """데이터 전처리"""
        processed_data = data.copy()

        # 결측값 처리
        if config.get('handle_missing', True):
            # 수치 컬럼만 선택
            numeric_columns = processed_data.select_dtypes(include=[np.number]).columns
            processed_data[numeric_columns] = processed_data[numeric_columns].fillna(processed_data[numeric_columns].mean())

        # 이상치 제거
        if config.get('remove_outliers', False):
            processed_data = self._remove_outliers(processed_data, config.get('outlier_method', 'iqr'))

        # 스케일링
        scaling_method = config.get('scaling', 'none')
        if scaling_method != 'none' and scaling_method in self.preprocessors:
            scaler_class = self.preprocessors[scaling_method]
            if scaler_class:
                scaler = scaler_class()
                numeric_columns = processed_data.select_dtypes(include=[np.number]).columns
                processed_data[numeric_columns] = scaler.fit_transform(processed_data[numeric_columns])

        return processed_data

    def _remove_outliers(self, data: pd.DataFrame, method: str = 'iqr') -> pd.DataFrame:
        """이상치 제거"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        if method == 'iqr':
            for col in numeric_columns:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                data = data[(data[col] >= lower_bound) & (data[col] <= upper_bound)]

        elif method == 'zscore':
            from scipy import stats
            z_scores = np.abs(stats.zscore(data[numeric_columns]))
            data = data[(z_scores < 3).all(axis=1)]

        return data

    def _apply_dimensionality_reduction(self, data: pd.DataFrame, config: Dict) -> Dict:
        """차원축소 적용"""
        method = config.get('method', 'pca')
        variables = config.get('variables', [])

        if not variables:
            # 수치 변수 자동 선택
            variables = data.select_dtypes(include=[np.number]).columns.tolist()

        if len(variables) < 2:
            raise ValueError("차원축소를 위해서는 최소 2개의 수치 변수가 필요합니다.")

        # 데이터 준비
        X = data[variables].dropna()

        if method in self.dimensionality_reducers:
            result = self.dimensionality_reducers[method](X, config)
            result['variables_used'] = variables
            result['original_shape'] = X.shape
            return result
        else:
            raise ValueError(f"지원하지 않는 차원축소 방법: {method}")

    def _apply_pca(self, X: pd.DataFrame, config: Dict) -> Dict:
        """PCA 적용"""
        n_components = config.get('n_components', 2)
        pca = PCA(n_components=n_components)
        X_reduced = pca.fit_transform(X)

        return {
            'method': 'pca',
            'reduced_data': X_reduced,
            'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
            'explained_variance_cumsum': np.cumsum(pca.explained_variance_ratio_).tolist(),
            'components': pca.components_.tolist(),
            'n_components': n_components
        }

    def _apply_tsne(self, X: pd.DataFrame, config: Dict) -> Dict:
        """t-SNE 적용"""
        n_components = config.get('n_components', 2)
        perplexity = config.get('perplexity', 30)
        learning_rate = config.get('learning_rate', 200)

        tsne = TSNE(n_components=n_components, perplexity=perplexity, learning_rate=learning_rate, random_state=42)
        X_reduced = tsne.fit_transform(X)

        return {
            'method': 'tsne',
            'reduced_data': X_reduced,
            'kl_divergence': tsne.kl_divergence_,
            'n_components': n_components,
            'perplexity': perplexity
        }

    def _apply_umap(self, X: pd.DataFrame, config: Dict) -> Dict:
        """UMAP 적용 (umap-learn 패키지 필요)"""
        try:
            import umap
            n_components = config.get('n_components', 2)
            n_neighbors = config.get('n_neighbors', 15)
            min_dist = config.get('min_dist', 0.1)

            reducer = umap.UMAP(n_components=n_components, n_neighbors=n_neighbors, min_dist=min_dist, random_state=42)
            X_reduced = reducer.fit_transform(X)

            return {
                'method': 'umap',
                'reduced_data': X_reduced,
                'n_components': n_components,
                'n_neighbors': n_neighbors,
                'min_dist': min_dist
            }
        except ImportError:
            raise ValueError("UMAP을 사용하려면 'umap-learn' 패키지가 필요합니다: pip install umap-learn")

    def _apply_clustering(self, data: pd.DataFrame, config: Dict) -> Dict:
        """클러스터링 적용"""
        method = config.get('method', 'kmeans')
        variables = config.get('variables', [])

        if not variables:
            variables = data.select_dtypes(include=[np.number]).columns.tolist()

        X = data[variables].dropna()

        if method in self.clusterers:
            result = self.clusterers[method](X, config)
            result['variables_used'] = variables
            return result
        else:
            raise ValueError(f"지원하지 않는 클러스터링 방법: {method}")

    def _apply_kmeans(self, X: pd.DataFrame, config: Dict) -> Dict:
        """K-means 클러스터링"""
        n_clusters = config.get('n_clusters', 3)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X)

        # 실루엣 점수 계산
        if len(set(clusters)) > 1:
            silhouette_avg = silhouette_score(X, clusters)
        else:
            silhouette_avg = 0

        return {
            'method': 'kmeans',
            'clusters': clusters.tolist(),
            'cluster_centers': kmeans.cluster_centers_.tolist(),
            'n_clusters': n_clusters,
            'inertia': kmeans.inertia_,
            'silhouette_score': silhouette_avg
        }

    def _apply_dbscan(self, X: pd.DataFrame, config: Dict) -> Dict:
        """DBSCAN 클러스터링"""
        eps = config.get('eps', 0.5)
        min_samples = config.get('min_samples', 5)

        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(X)

        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        n_noise = list(clusters).count(-1)

        return {
            'method': 'dbscan',
            'clusters': clusters.tolist(),
            'n_clusters': n_clusters,
            'n_noise_points': n_noise,
            'eps': eps,
            'min_samples': min_samples
        }

    def _apply_hierarchical(self, X: pd.DataFrame, config: Dict) -> Dict:
        """계층적 클러스터링"""
        from sklearn.cluster import AgglomerativeClustering

        n_clusters = config.get('n_clusters', 3)
        linkage = config.get('linkage', 'ward')

        hierarchical = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
        clusters = hierarchical.fit_predict(X)

        return {
            'method': 'hierarchical',
            'clusters': clusters.tolist(),
            'n_clusters': n_clusters,
            'linkage': linkage
        }

    def _create_visualization(self, data: pd.DataFrame, config: Dict, analysis_results: Dict) -> Dict:
        """시각화 생성"""
        viz_type = config.get('type', 'scatter')

        if viz_type in self.visualizers:
            fig = self.visualizers[viz_type](data, config, analysis_results)
            return {
                'type': viz_type,
                'config': config,
                'figure': fig
            }
        else:
            raise ValueError(f"지원하지 않는 시각화 타입: {viz_type}")

    def _create_scatter_plot(self, data: pd.DataFrame, config: Dict, analysis_results: Dict) -> go.Figure:
        """산점도 생성"""
        x_var = config.get('x_axis')
        y_var = config.get('y_axis')
        color_var = config.get('color_by')

        # 차원축소 결과 사용
        if config.get('use_dimensionality_reduction') and 'dimensionality_reduction' in analysis_results:
            dr_result = analysis_results['dimensionality_reduction']
            reduced_data = dr_result['reduced_data']

            plot_data = data.copy()
            plot_data['component_1'] = reduced_data[:, 0]
            plot_data['component_2'] = reduced_data[:, 1]

            x_var = 'component_1'
            y_var = 'component_2'

        # 클러스터링 결과 사용
        if config.get('use_clustering') and 'clustering' in analysis_results:
            cluster_result = analysis_results['clustering']
            plot_data = data.copy()
            plot_data['cluster'] = cluster_result['clusters']
            if not color_var:
                color_var = 'cluster'

        if not x_var or not y_var:
            raise ValueError("X축과 Y축 변수를 지정해야 합니다.")

        # Plotly 산점도 생성
        fig = px.scatter(
            plot_data,
            x=x_var,
            y=y_var,
            color=color_var,
            hover_data=['name'] if 'name' in plot_data.columns else None,
            title=config.get('title', f'{y_var} vs {x_var}'),
            color_continuous_scale=config.get('color_scale', 'viridis')
        )

        fig.update_layout(
            width=config.get('width', 800),
            height=config.get('height', 600)
        )

        return fig

    def _create_3d_scatter_plot(self, data: pd.DataFrame, config: Dict, analysis_results: Dict) -> go.Figure:
        """3D 산점도 생성"""
        x_var = config.get('x_axis')
        y_var = config.get('y_axis')
        z_var = config.get('z_axis')
        color_var = config.get('color_by')

        # 차원축소 결과 사용 (3D)
        if config.get('use_dimensionality_reduction') and 'dimensionality_reduction' in analysis_results:
            dr_result = analysis_results['dimensionality_reduction']
            if dr_result.get('n_components', 2) >= 3:
                reduced_data = dr_result['reduced_data']
                plot_data = data.copy()
                plot_data['component_1'] = reduced_data[:, 0]
                plot_data['component_2'] = reduced_data[:, 1]
                plot_data['component_3'] = reduced_data[:, 2]

                x_var = 'component_1'
                y_var = 'component_2'
                z_var = 'component_3'

        fig = px.scatter_3d(
            data,
            x=x_var,
            y=y_var,
            z=z_var,
            color=color_var,
            title=config.get('title', f'3D Plot: {x_var}, {y_var}, {z_var}')
        )

        return fig

    def _create_heatmap(self, data: pd.DataFrame, config: Dict, analysis_results: Dict) -> go.Figure:
        """히트맵 생성"""
        variables = config.get('variables', [])
        if not variables:
            variables = data.select_dtypes(include=[np.number]).columns.tolist()

        correlation_matrix = data[variables].corr()

        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            title=config.get('title', 'Correlation Heatmap')
        )

        return fig

    def _create_histogram(self, data: pd.DataFrame, config: Dict, analysis_results: Dict) -> go.Figure:
        """히스토그램 생성"""
        variable = config.get('variable')
        if not variable:
            raise ValueError("히스토그램을 위한 변수를 지정해야 합니다.")

        fig = px.histogram(
            data,
            x=variable,
            nbins=config.get('bins', 30),
            title=config.get('title', f'{variable} Distribution')
        )

        return fig

    def _create_box_plot(self, data: pd.DataFrame, config: Dict, analysis_results: Dict) -> go.Figure:
        """박스플롯 생성"""
        variable = config.get('variable')
        group_by = config.get('group_by')

        fig = px.box(
            data,
            y=variable,
            x=group_by,
            title=config.get('title', f'{variable} Box Plot')
        )

        return fig

    def _create_violin_plot(self, data: pd.DataFrame, config: Dict, analysis_results: Dict) -> go.Figure:
        """바이올린 플롯 생성"""
        variable = config.get('variable')
        group_by = config.get('group_by')

        fig = px.violin(
            data,
            y=variable,
            x=group_by,
            title=config.get('title', f'{variable} Violin Plot')
        )

        return fig

    def _calculate_statistics(self, data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """통계 계산"""
        stats = {
            'total_records': len(data),
            'total_variables': len(data.columns),
            'numeric_variables': len(data.select_dtypes(include=[np.number]).columns)
        }

        # 클러스터링 통계
        if 'clustering' in analysis_results:
            cluster_result = analysis_results['clustering']
            clusters = cluster_result['clusters']
            stats['clustering'] = {
                'n_clusters': len(set(clusters)),
                'cluster_distribution': {str(i): clusters.count(i) for i in set(clusters)},
                'silhouette_score': cluster_result.get('silhouette_score')
            }

        # 차원축소 통계
        if 'dimensionality_reduction' in analysis_results:
            dr_result = analysis_results['dimensionality_reduction']
            stats['dimensionality_reduction'] = {
                'method': dr_result['method'],
                'explained_variance': dr_result.get('explained_variance_ratio'),
                'cumulative_variance': dr_result.get('explained_variance_cumsum')
            }

        return stats

    def _generate_config_hash(self, config: Dict) -> str:
        """설정 해시 생성"""
        config_string = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_string.encode()).hexdigest()

    def get_analysis_templates(self) -> Dict:
        """분석 템플릿 반환"""
        return {
            "basic_ratio_pca": {
                "name": "기본 비율 PCA 분석",
                "description": "얼굴 비율 데이터의 PCA 분석 및 시각화",
                "config": {
                    "preprocessing": {"scaling": "standard", "remove_outliers": True},
                    "dimensionality_reduction": {"method": "pca", "n_components": 2},
                    "visualizations": [
                        {"type": "scatter", "use_dimensionality_reduction": True, "title": "PCA Results"}
                    ]
                }
            },
            "clustering_analysis": {
                "name": "클러스터링 분석",
                "description": "K-means 클러스터링과 시각화",
                "config": {
                    "preprocessing": {"scaling": "standard"},
                    "clustering": {"method": "kmeans", "n_clusters": 3},
                    "visualizations": [
                        {"type": "scatter", "use_clustering": True, "title": "Clustering Results"}
                    ]
                }
            },
            "pca_clustering_combo": {
                "name": "PCA + 클러스터링 조합",
                "description": "PCA 차원축소 후 클러스터링 수행",
                "config": {
                    "preprocessing": {"scaling": "standard", "remove_outliers": True},
                    "dimensionality_reduction": {"method": "pca", "n_components": 2},
                    "clustering": {"method": "kmeans", "n_clusters": 3},
                    "visualizations": [
                        {"type": "scatter", "use_dimensionality_reduction": True, "use_clustering": True, "title": "PCA + Clustering"}
                    ]
                }
            }
        }