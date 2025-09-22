"""
클러스터링 분석 유틸리티
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional


def perform_kmeans_clustering(df: pd.DataFrame, n_clusters: int = 3,
                            x_col: str = 'x_axis', y_col: str = 'y_axis') -> pd.DataFrame:
    """
    K-means 클러스터링 수행

    Args:
        df: 입력 DataFrame
        n_clusters: 클러스터 개수
        x_col: X축 컬럼명
        y_col: Y축 컬럼명

    Returns:
        클러스터 정보가 추가된 DataFrame
    """
    if df.empty or len(df) < n_clusters:
        return df

    # 클러스터링할 데이터 준비
    features = df[[x_col, y_col]].copy()

    # 결측값 제거
    features = features.dropna()

    if len(features) < n_clusters:
        return df

    try:
        # K-means 클러스터링
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(features)

        # 결과를 원본 DataFrame에 추가
        result_df = df.copy()
        result_df['cluster'] = -1  # 기본값

        # 유효한 데이터에만 클러스터 라벨 할당
        valid_indices = features.index
        result_df.loc[valid_indices, 'cluster'] = cluster_labels

        # 클러스터 센터 정보 추가
        result_df._cluster_centers = kmeans.cluster_centers_
        result_df._kmeans_model = kmeans

        return result_df

    except Exception as e:
        print(f"Clustering error: {e}")
        return df


def calculate_cluster_statistics(df: pd.DataFrame,
                               x_col: str = 'x_axis',
                               y_col: str = 'y_axis') -> Dict:
    """
    클러스터별 통계 계산

    Args:
        df: 클러스터링된 DataFrame
        x_col: X축 컬럼명
        y_col: Y축 컬럼명

    Returns:
        클러스터 통계 딕셔너리
    """
    if 'cluster' not in df.columns:
        return {}

    stats = {}

    # 클러스터별 통계 계산
    for cluster_id in sorted(df['cluster'].unique()):
        if cluster_id == -1:  # 유효하지 않은 클러스터 제외
            continue

        cluster_data = df[df['cluster'] == cluster_id]

        if len(cluster_data) == 0:
            continue

        x_values = cluster_data[x_col].dropna()
        y_values = cluster_data[y_col].dropna()

        stats[cluster_id] = {
            'count': len(cluster_data),
            'x_mean': x_values.mean() if len(x_values) > 0 else 0,
            'x_std': x_values.std() if len(x_values) > 0 else 0,
            'y_mean': y_values.mean() if len(y_values) > 0 else 0,
            'y_std': y_values.std() if len(y_values) > 0 else 0,
            'names': cluster_data['name'].tolist(),
            'tags': cluster_data['tags'].tolist()
        }

        # 클러스터 품질 지표 계산
        if len(x_values) > 1 and len(y_values) > 1:
            # 클러스터 내 분산 (작을수록 응집도 높음)
            intra_cluster_variance = (x_values.var() + y_values.var()) / 2
            stats[cluster_id]['variance'] = intra_cluster_variance

            # 의미있는 특성 판별 (표준편차가 작을수록 의미있음)
            combined_std = (stats[cluster_id]['x_std'] + stats[cluster_id]['y_std']) / 2
            stats[cluster_id]['significance_score'] = 1 / (1 + combined_std)  # 높을수록 의미있음

    return stats


def get_cluster_recommendations(stats: Dict, threshold: float = 0.5) -> List[Dict]:
    """
    의미있는 클러스터 추천

    Args:
        stats: 클러스터 통계
        threshold: 의미도 임계값

    Returns:
        추천 클러스터 정보 리스트
    """
    recommendations = []

    for cluster_id, cluster_stats in stats.items():
        significance = cluster_stats.get('significance_score', 0)
        count = cluster_stats.get('count', 0)

        if significance > threshold and count >= 2:
            recommendations.append({
                'cluster_id': cluster_id,
                'significance_score': significance,
                'count': count,
                'x_std': cluster_stats.get('x_std', 0),
                'y_std': cluster_stats.get('y_std', 0),
                'description': f"클러스터 {cluster_id}: 높은 유사성 (의미도: {significance:.3f})"
            })

    # 의미도 순으로 정렬
    recommendations.sort(key=lambda x: x['significance_score'], reverse=True)

    return recommendations


def analyze_cluster_separation(df: pd.DataFrame, x_col: str = 'x_axis', y_col: str = 'y_axis') -> Dict:
    """
    클러스터 간 분리도 분석

    Args:
        df: 클러스터링된 DataFrame
        x_col: X축 컬럼명
        y_col: Y축 컬럼명

    Returns:
        분리도 분석 결과
    """
    if 'cluster' not in df.columns or df['cluster'].nunique() < 2:
        return {}

    try:
        # 클러스터 센터 간 거리 계산
        unique_clusters = [c for c in df['cluster'].unique() if c != -1]

        if len(unique_clusters) < 2:
            return {}

        centers = []
        for cluster_id in unique_clusters:
            cluster_data = df[df['cluster'] == cluster_id]
            x_center = cluster_data[x_col].mean()
            y_center = cluster_data[y_col].mean()
            centers.append([x_center, y_center])

        centers = np.array(centers)

        # 센터 간 평균 거리
        distances = []
        for i in range(len(centers)):
            for j in range(i + 1, len(centers)):
                dist = np.linalg.norm(centers[i] - centers[j])
                distances.append(dist)

        avg_inter_cluster_distance = np.mean(distances) if distances else 0

        # 클러스터 내 평균 거리
        intra_cluster_distances = []
        for cluster_id in unique_clusters:
            cluster_data = df[df['cluster'] == cluster_id]
            if len(cluster_data) > 1:
                cluster_center = [cluster_data[x_col].mean(), cluster_data[y_col].mean()]
                for _, row in cluster_data.iterrows():
                    point = [row[x_col], row[y_col]]
                    dist = np.linalg.norm(np.array(point) - np.array(cluster_center))
                    intra_cluster_distances.append(dist)

        avg_intra_cluster_distance = np.mean(intra_cluster_distances) if intra_cluster_distances else 0

        # 실루엣 스코어 근사값 (높을수록 좋음)
        silhouette_approx = 0
        if avg_intra_cluster_distance > 0:
            silhouette_approx = (avg_inter_cluster_distance - avg_intra_cluster_distance) / max(avg_inter_cluster_distance, avg_intra_cluster_distance)

        return {
            'avg_inter_cluster_distance': avg_inter_cluster_distance,
            'avg_intra_cluster_distance': avg_intra_cluster_distance,
            'silhouette_approx': silhouette_approx,
            'cluster_quality': 'Good' if silhouette_approx > 0.3 else 'Fair' if silhouette_approx > 0 else 'Poor'
        }

    except Exception as e:
        print(f"Cluster separation analysis error: {e}")
        return {}