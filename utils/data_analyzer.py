"""
데이터 분석 및 시각화 유틸리티
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json
from .landmark_calculator import calculate_length, calculate_curvature


def execute_length_based_analysis(landmarks_data, l1_p1, l1_p2, l1_calc, l2_p1, l2_p2, l2_calc, purpose,
                                   normalize_ratio=False, swap_axes=False, enable_tag_highlight=False, selected_tags=None, point_group=None):
    """길이 기반 분석 실행"""
    if selected_tags is None:
        selected_tags = []
    st.write("### 🔄 분석 실행 중...")

    # 각 데이터에 대해 길이1, 길이2 계산
    length1_values = []
    length2_values = []
    names = []
    tags_list = []
    colors = []

    # 태그별 컬러 매핑 생성
    if enable_tag_highlight:
        all_tags = set()
        for _, row in landmarks_data.iterrows():
            if 'tags' in row and row['tags']:
                tags = row['tags'] if isinstance(row['tags'], list) else []
                all_tags.update(tags)

        # 태그별 고유 색상 생성
        color_palette = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel + px.colors.qualitative.Set1
        tag_color_map = {tag: color_palette[i % len(color_palette)] for i, tag in enumerate(sorted(all_tags))}
        tag_color_map['기타'] = '#808080'  # 회색

    for _, row in landmarks_data.iterrows():
        try:
            # 랜드마크 데이터 파싱
            if isinstance(row['landmarks'], str):
                landmarks = json.loads(row['landmarks'])
            else:
                landmarks = row['landmarks']

            if purpose == "🌊 곡률 분석":
                # 곡률 분석: 점 그룹의 곡률 계산
                curvatures = calculate_curvature(landmarks, point_group)
                if curvatures is not None:
                    # 곡률 분석에서는 각 점별로 곡률 데이터를 저장
                    for i, curvature in enumerate(curvatures):
                        length1_values.append(i)  # X축: 점 인덱스 (0, 1, 2, ...)
                        length2_values.append(round(curvature, 4))  # Y축: 곡률값
                        names.append(f"{row['name']}_점{i}")
                        # 태그 정보 수집
                        row_tags = []
                        if 'tags' in row and row['tags']:
                            row_tags = row['tags'] if isinstance(row['tags'], list) else []
                        tags_list.append(', '.join(row_tags) if row_tags else '태그없음')

                        # 색상 결정
                        if enable_tag_highlight and selected_tags:
                            matching_tags = [tag for tag in selected_tags if tag in row_tags]
                            if matching_tags:
                                color = tag_color_map.get(matching_tags[0], '#FF0000')
                            else:
                                color = '#808080'  # 회색으로 dimmed
                        else:
                            color = '#808080'  # 기본 회색
                        colors.append(color)
            else:
                # 기존 길이/비율 계산
                length1 = calculate_length(landmarks, l1_p1, l1_p2, l1_calc)
                length2 = calculate_length(landmarks, l2_p1, l2_p2, l2_calc)

                if length1 is not None and (length2 is not None or purpose == "📏 거리 측정"):
                    final_length1 = length1
                    final_length2 = length2 if length2 is not None else 0

                    # 정규화 적용 (비율 계산이고 normalize_ratio가 True일 때)
                    if purpose == "⚖️ 비율 계산" and normalize_ratio and final_length1 != 0:
                        # X축(길이1)을 1로 고정하고 Y축(길이2)을 비례적으로 스케일링
                        scale_factor = final_length1
                        final_length1 = 1.0
                        final_length2 = final_length2 / scale_factor if scale_factor != 0 else 0

                    # 소수점 둘째자리까지 반올림
                    final_length1 = round(final_length1, 2)
                    final_length2 = round(final_length2, 2)

                    # 태그 정보 수집
                    row_tags = []
                    if 'tags' in row and row['tags']:
                        row_tags = row['tags'] if isinstance(row['tags'], list) else []

                    # 색상 결정
                    if enable_tag_highlight and selected_tags:
                        # 특정 태그들이 선택된 경우에만 색상 적용
                        matching_tags = [tag for tag in selected_tags if tag in row_tags]
                        if matching_tags:
                            # 선택된 태그 중 첫 번째 매칭되는 태그의 색상 사용
                            color = tag_color_map.get(matching_tags[0], '#FF0000')
                            opacity = 1.0
                        else:
                            color = '#808080'  # 회색으로 dimmed
                            opacity = 0.6
                    else:
                        # 기본 회색 (태그 하이라이트 비활성화 또는 태그 미선택 시)
                        color = '#808080'  # 회색
                        opacity = 1.0

                    length1_values.append(final_length1)
                    length2_values.append(final_length2)
                    names.append(row['name'])
                    tags_list.append(', '.join(row_tags) if row_tags else '태그없음')
                    colors.append(color)

        except Exception as e:
            st.error(f"데이터 처리 오류 ({row['name']}): {e}")
            continue

    if not length1_values:
        st.error("❌ 계산할 수 있는 데이터가 없습니다.")
        return

    # 결과 표시
    st.write("### 📊 분석 결과")

    # 결과 데이터프레임 생성
    result_df = pd.DataFrame({
        'name': names,
        'length1': length1_values,
        'length2': length2_values,
        'tags': tags_list,
        'color': colors
    })

    # 모든 경우에 산점도로 표시
    col1, col2 = st.columns([2, 1])

    with col1:
        if purpose == "🌊 곡률 분석":
            # 곡률 분석인 경우: X축 - 점 인덱스, Y축 - 곡률값의 선 그래프
            title = f'곡률 분석 결과'
            x_label = f'점 인덱스'
            y_label = f'곡률 값'

            if enable_tag_highlight:
                fig = go.Figure()

                # 각 얼굴별로 곡률 곡선을 그룹화
                face_groups = {}
                for idx, row in result_df.iterrows():
                    face_name = row['name'].split('_점')[0]  # '_점N' 제거
                    if face_name not in face_groups:
                        face_groups[face_name] = {'x': [], 'y': [], 'color': row['color'], 'tags': ''}
                    face_groups[face_name]['x'].append(row['length1'])
                    face_groups[face_name]['y'].append(row['length2'])
                    face_groups[face_name]['tags'] = row['tags']

                # 각 얼굴별 곡률 곡선 추가
                for face_name, data in face_groups.items():
                    fig.add_trace(go.Scatter(
                        x=data['x'],
                        y=data['y'],
                        mode='lines+markers',
                        line=dict(color=data['color'], width=2),
                        marker=dict(color=data['color'], size=6),
                        name=face_name,
                        hovertemplate=f"얼굴: {face_name}<br>태그: {data['tags']}<br>점 인덱스: %{{x}}<br>곡률: %{{y}}<extra></extra>"
                    ))

                # y=0 기준선 추가 (볼록/오목 구분)
                fig.add_hline(y=0, line_dash="dash", line_color="gray",
                             annotation_text="기준선 (y=0)", annotation_position="bottom right")

                fig.update_layout(
                    title=title,
                    xaxis_title=x_label,
                    yaxis_title=y_label + " (양수: ∩볼록, 음수: ∪오목)",
                    showlegend=True
                )
            else:
                # 기본 선 그래프 (태그 하이라이트 비활성화)
                fig = go.Figure()

                # 각 얼굴별로 곡률 곡선을 그룹화
                face_groups = {}
                for idx, row in result_df.iterrows():
                    face_name = row['name'].split('_점')[0]
                    if face_name not in face_groups:
                        face_groups[face_name] = {'x': [], 'y': [], 'tags': ''}
                    face_groups[face_name]['x'].append(row['length1'])
                    face_groups[face_name]['y'].append(row['length2'])
                    face_groups[face_name]['tags'] = row['tags']

                for face_name, data in face_groups.items():
                    fig.add_trace(go.Scatter(
                        x=data['x'],
                        y=data['y'],
                        mode='lines+markers',
                        line=dict(color='#808080', width=2),
                        marker=dict(color='#808080', size=6),
                        name=face_name,
                        hovertemplate=f"얼굴: {face_name}<br>태그: {data['tags']}<br>점 인덱스: %{{x}}<br>곡률: %{{y}}<extra></extra>"
                    ))

                # y=0 기준선 추가 (볼록/오목 구분)
                fig.add_hline(y=0, line_dash="dash", line_color="gray",
                             annotation_text="기준선 (y=0)", annotation_position="bottom right")

                fig.update_layout(
                    title=title,
                    xaxis_title=x_label,
                    yaxis_title=y_label + " (양수: ∩볼록, 음수: ∪오목)",
                    showlegend=True
                )

        elif purpose == "⚖️ 비율 계산":
            # 비율 계산인 경우: X축 - 길이1, Y축 - 길이2의 산점도

            # 축 바꾸기 적용
            if swap_axes:
                x_data, y_data = 'length2', 'length1'
                if normalize_ratio:
                    title = f'정규화된 비율 (Y : 1)'
                    x_label = f'길이2 (정규화 비율)'
                    y_label = f'길이1 (정규화됨)'
                else:
                    title = f'길이2 vs 길이1'
                    x_label = f'길이2 ({l2_calc})'
                    y_label = f'길이1 ({l1_calc})'
            else:
                x_data, y_data = 'length1', 'length2'
                if normalize_ratio:
                    title = f'정규화된 비율 (1 : Y)'
                    x_label = f'길이1 (정규화됨)'
                    y_label = f'길이2 (정규화 비율)'
                else:
                    title = f'길이1 vs 길이2'
                    x_label = f'길이1 ({l1_calc})'
                    y_label = f'길이2 ({l2_calc})'

            # 태그 하이라이트가 활성화되어 있으면 색상 적용
            if enable_tag_highlight:
                fig = go.Figure()

                # 각 점을 개별적으로 추가하여 색상 제어
                for idx, row in result_df.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[row[x_data]],
                        y=[row[y_data]],
                        mode='markers',
                        marker=dict(
                            color=row['color'],
                            size=8,
                            opacity=0.8,
                            line=dict(width=1, color='white')
                        ),
                        hovertemplate=f"이름: {row['name']}<br>태그: {row['tags']}<br>길이1: {row['length1']}<br>길이2: {row['length2']}<extra></extra>",
                        showlegend=False,
                        name=row['name']
                    ))

                fig.update_layout(
                    title=title,
                    xaxis_title=x_label,
                    yaxis_title=y_label
                )
            else:
                fig = px.scatter(
                    result_df,
                    x=x_data,
                    y=y_data,
                    title=title,
                    labels={x_data: x_label, y_data: y_label},
                    hover_data=['name', 'tags']
                )
        else:
            # 거리 측정인 경우: 히스토그램 대신 strip plot(산점도)로 변경하여 hover 지원
            # Y축에 약간의 랜덤 지터 추가하여 점들이 겹치지 않게 함
            np.random.seed(42)  # 일관된 결과를 위해
            result_df['y_jitter'] = np.random.uniform(-0.1, 0.1, len(result_df))

            if enable_tag_highlight:
                fig = go.Figure()

                # 각 점을 개별적으로 추가하여 색상 제어
                for idx, row in result_df.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[row['length1']],
                        y=[row['y_jitter']],
                        mode='markers',
                        marker=dict(
                            color=row['color'],
                            size=8,
                            opacity=0.8,
                            line=dict(width=1, color='white')
                        ),
                        hovertemplate=f"이름: {row['name']}<br>태그: {row['tags']}<br>길이1: {row['length1']}<br>길이2: {row['length2']}<extra></extra>",
                        showlegend=False,
                        name=row['name']
                    ))

                fig.update_layout(
                    title=f'거리 분포 ({l1_calc}) - 태그별 색상 구분',
                    xaxis_title=f'거리 ({l1_calc})',
                    yaxis_title=""
                )
                # Y축 숨기기 (의미없는 축이므로)
                fig.update_yaxes(showticklabels=False)
            else:
                fig = px.scatter(
                    result_df,
                    x='length1',
                    y='y_jitter',
                    title=f'거리 분포 ({l1_calc}) - 각 점이 개별 데이터',
                    labels={'length1': f'거리 ({l1_calc})', 'y_jitter': '분산 (시각화용)'},
                    hover_data=['name', 'tags']
                )
                # Y축 숨기기 (의미없는 축이므로)
                fig.update_yaxes(showticklabels=False, title_text="")

        st.plotly_chart(fig, use_container_width=True)

        # 태그 하이라이트가 활성화되어 있으면 태그 범례 표시
        if enable_tag_highlight:
            st.write("#### 🏷️ 태그 범례")

            # 현재 데이터의 태그별 개수 계산
            tag_counts = {}
            for tags_str in tags_list:
                if tags_str != '태그없음':
                    for tag in tags_str.split(', '):
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                else:
                    tag_counts['태그없음'] = tag_counts.get('태그없음', 0) + 1

            # 태그별 색상 박스와 개수 표시
            cols = st.columns(min(4, len(tag_counts)))
            for i, (tag, count) in enumerate(sorted(tag_counts.items())):
                with cols[i % len(cols)]:
                    if enable_tag_highlight:
                        color = tag_color_map.get(tag, '#808080')
                        # HTML을 사용해 색상 박스 표시
                        st.markdown(
                            f'<div style="display: flex; align-items: center;">'
                            f'<div style="width: 20px; height: 20px; background-color: {color}; '
                            f'border: 1px solid #ccc; margin-right: 8px; border-radius: 3px;"></div>'
                            f'<span><strong>{tag}</strong> ({count}개)</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            # 필터링 정보 표시
            if selected_tags:
                st.info(f"🎯 선택된 태그: {', '.join(selected_tags)} (선택된 태그만 색상으로 표시)")
            else:
                st.info("💡 모든 점이 회색으로 표시됩니다. 특정 태그를 색상으로 하이라이트하려면 위에서 선택하세요.")

    with col2:
        if purpose == "🌊 곡률 분석":
            st.write("#### 📈 곡률 통계")
            st.write(f"**평균:** {np.mean(length2_values):.4f}")
            st.write(f"**표준편차:** {np.std(length2_values):.4f}")
            st.write(f"**최소값:** {np.min(length2_values):.4f}")
            st.write(f"**최대값:** {np.max(length2_values):.4f}")
            st.write(f"**총 점 개수:** {len(length2_values)}개")
        elif purpose == "📏 거리 측정":
            st.write("#### 📈 거리 통계")
            st.write(f"**평균:** {np.mean(length1_values):.2f}")
            st.write(f"**표준편차:** {np.std(length1_values):.2f}")
            st.write(f"**최소값:** {np.min(length1_values):.2f}")
            st.write(f"**최대값:** {np.max(length1_values):.2f}")
            st.write(f"**유니크 값:** {len(set(length1_values))}개")
        else:
            st.write("#### 📈 길이1 통계")
            st.write(f"**평균:** {np.mean(length1_values):.2f}")
            st.write(f"**표준편차:** {np.std(length1_values):.2f}")

            st.write("#### 📈 길이2 통계")
            st.write(f"**평균:** {np.mean(length2_values):.2f}")
            st.write(f"**표준편차:** {np.std(length2_values):.2f}")

    # 상세 데이터 테이블
    with st.expander("📋 상세 데이터 보기"):
        # 색상 컬럼 제거 후 표시
        display_df = result_df.drop('color', axis=1) if 'color' in result_df.columns else result_df
        st.dataframe(display_df, use_container_width=True)

        # 태그별 통계
        if enable_tag_highlight and tags_list:
            st.write("##### 📊 태그별 통계")
            tag_stats = {}
            for i, tags_str in enumerate(tags_list):
                if tags_str != '태그없음':
                    primary_tag = tags_str.split(', ')[0]
                    if primary_tag not in tag_stats:
                        tag_stats[primary_tag] = {'count': 0, 'values': []}
                    tag_stats[primary_tag]['count'] += 1
                    tag_stats[primary_tag]['values'].append(length1_values[i])

            if tag_stats:
                stats_data = []
                for tag, data in tag_stats.items():
                    stats_data.append({
                        '태그': tag,
                        '개수': data['count'],
                        '평균': f"{np.mean(data['values']):.2f}",
                        '표준편차': f"{np.std(data['values']):.2f}",
                        '최소값': f"{np.min(data['values']):.2f}",
                        '최대값': f"{np.max(data['values']):.2f}"
                    })
                st.dataframe(pd.DataFrame(stats_data), use_container_width=True)