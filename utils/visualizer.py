"""
시각화 유틸리티
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def create_scatter_plot(df: pd.DataFrame,
                       x_col: str = 'x_axis',
                       y_col: str = 'y_axis',
                       color_col: Optional[str] = None,
                       title: str = "얼굴 비율 분포") -> go.Figure:
    """
    기본 산점도 생성

    Args:
        df: 데이터 DataFrame
        x_col: X축 컬럼명
        y_col: Y축 컬럼명
        color_col: 색상 구분 컬럼명
        title: 그래프 제목

    Returns:
        Plotly Figure 객체
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="데이터가 없습니다.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig

    # 호버 정보 구성
    hover_data = {
        'name': True,
        'tags': True,
        'face_ratio_str': True,
        'roll_angle': True
    }

    if color_col and color_col in df.columns:
        fig = px.scatter(
            df, x=x_col, y=y_col,
            color=color_col,
            hover_name='name',
            hover_data=hover_data,
            title=title,
            labels={
                x_col: f'비율 2번째 값 ({x_col})',
                y_col: f'비율 3번째 값 ({y_col})'
            }
        )
    else:
        fig = px.scatter(
            df, x=x_col, y=y_col,
            hover_name='name',
            hover_data=hover_data,
            title=title,
            labels={
                x_col: f'비율 2번째 값 ({x_col})',
                y_col: f'비율 3번째 값 ({y_col})'
            }
        )

    # 레이아웃 개선
    fig.update_layout(
        width=800,
        height=600,
        showlegend=True if color_col else False
    )

    # 축 설정
    fig.update_xaxes(title_font_size=14)
    fig.update_yaxes(title_font_size=14)

    return fig


def create_cluster_plot(df: pd.DataFrame,
                       x_col: str = 'x_axis',
                       y_col: str = 'y_axis',
                       n_clusters: int = 3) -> go.Figure:
    """
    클러스터링 결과 시각화

    Args:
        df: 클러스터링된 DataFrame
        x_col: X축 컬럼명
        y_col: Y축 컬럼명
        n_clusters: 클러스터 개수

    Returns:
        Plotly Figure 객체
    """
    if 'cluster' not in df.columns:
        return create_scatter_plot(df, x_col, y_col, title="클러스터링 실패")

    # 클러스터별 색상 지정
    fig = px.scatter(
        df[df['cluster'] != -1],  # 유효한 클러스터만
        x=x_col, y=y_col,
        color='cluster',
        hover_name='name',
        hover_data={
            'tags': True,
            'face_ratio_str': True,
            'roll_angle': True,
            'cluster': True
        },
        title=f"얼굴 비율 클러스터링 (K={n_clusters})",
        labels={
            x_col: f'비율 2번째 값 ({x_col})',
            y_col: f'비율 3번째 값 ({y_col})',
            'cluster': '클러스터'
        },
        color_discrete_sequence=px.colors.qualitative.Set1
    )

    # 클러스터 센터 표시 (가능한 경우)
    if hasattr(df, '_cluster_centers'):
        centers = df._cluster_centers
        for i, center in enumerate(centers):
            fig.add_trace(go.Scatter(
                x=[center[0]],
                y=[center[1]],
                mode='markers',
                marker=dict(
                    symbol='x',
                    size=15,
                    color='black',
                    line=dict(width=2)
                ),
                name=f'센터 {i}',
                showlegend=True
            ))

    fig.update_layout(
        width=800,
        height=600,
        showlegend=True
    )

    return fig


def create_cluster_statistics_chart(stats: Dict) -> go.Figure:
    """
    클러스터 통계 차트 생성

    Args:
        stats: 클러스터 통계 딕셔너리

    Returns:
        Plotly Figure 객체
    """
    if not stats:
        fig = go.Figure()
        fig.add_annotation(
            text="클러스터 통계를 계산할 수 없습니다.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig

    # 서브플롯 생성
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '클러스터별 데이터 개수',
            'X축 표준편차',
            'Y축 표준편차',
            '의미도 점수'
        ),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )

    cluster_ids = list(stats.keys())
    counts = [stats[cid]['count'] for cid in cluster_ids]
    x_stds = [stats[cid]['x_std'] for cid in cluster_ids]
    y_stds = [stats[cid]['y_std'] for cid in cluster_ids]
    significance = [stats[cid].get('significance_score', 0) for cid in cluster_ids]

    # 각 서브플롯에 데이터 추가
    fig.add_trace(
        go.Bar(x=cluster_ids, y=counts, name='개수'),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(x=cluster_ids, y=x_stds, name='X축 SD'),
        row=1, col=2
    )

    fig.add_trace(
        go.Bar(x=cluster_ids, y=y_stds, name='Y축 SD'),
        row=2, col=1
    )

    fig.add_trace(
        go.Bar(x=cluster_ids, y=significance, name='의미도'),
        row=2, col=2
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        title_text="클러스터 통계 분석"
    )

    return fig


def create_distribution_plot(df: pd.DataFrame,
                           col: str,
                           title: str = "분포 히스토그램") -> go.Figure:
    """
    분포 히스토그램 생성

    Args:
        df: 데이터 DataFrame
        col: 히스토그램을 그릴 컬럼명
        title: 그래프 제목

    Returns:
        Plotly Figure 객체
    """
    if df.empty or col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text=f"컬럼 '{col}'의 데이터가 없습니다.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig

    fig = px.histogram(
        df, x=col,
        title=title,
        nbins=20,
        labels={col: col}
    )

    fig.update_layout(
        width=600,
        height=400
    )

    return fig


def create_correlation_heatmap(df: pd.DataFrame,
                             numeric_cols: List[str]) -> go.Figure:
    """
    상관관계 히트맵 생성

    Args:
        df: 데이터 DataFrame
        numeric_cols: 수치형 컬럼 리스트

    Returns:
        Plotly Figure 객체
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="데이터가 없습니다.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig

    # 상관계수 계산
    available_cols = [col for col in numeric_cols if col in df.columns]

    if len(available_cols) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="상관관계를 계산할 수치형 컬럼이 부족합니다.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig

    corr_matrix = df[available_cols].corr()

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))

    fig.update_layout(
        title="변수 간 상관관계",
        width=500,
        height=500
    )

    return fig