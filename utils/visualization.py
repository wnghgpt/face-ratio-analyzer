"""
시각화 유틸리티
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from .tag_processor import sort_by_frequency


def create_sankey_diagram(relationships, selected_abstract_tag="전체", min_frequency=2, relationship_type="전체 흐름 (추상→1차→2차)", selected_primary_tag="전체"):
    """Sankey 다이어그램 생성"""

    # 관계 타입에 따른 데이터 필터링
    filtered_abs_to_prim = {}
    filtered_prim_to_sec = {}

    if relationship_type == "1차→2차만":
        # 1차→2차 관계만 표시
        if selected_primary_tag != "전체":
            # 다중 선택 처리
            if isinstance(selected_primary_tag, list):
                filtered_prim_to_sec = {k: v for k, v in relationships['primary_to_secondary'].items()
                                      if k[0] in selected_primary_tag and v >= min_frequency}
            else:
                filtered_prim_to_sec = {k: v for k, v in relationships['primary_to_secondary'].items()
                                      if k[0] == selected_primary_tag and v >= min_frequency}
        else:
            filtered_prim_to_sec = {k: v for k, v in relationships['primary_to_secondary'].items() if v >= min_frequency}

    elif relationship_type == "추상→1차만":
        # 추상→1차 관계만 표시
        if selected_abstract_tag != "전체":
            # 다중 선택 처리
            if isinstance(selected_abstract_tag, list):
                filtered_abs_to_prim = {k: v for k, v in relationships['abstract_to_primary'].items()
                                      if k[0] in selected_abstract_tag and v >= min_frequency}
            else:
                filtered_abs_to_prim = {k: v for k, v in relationships['abstract_to_primary'].items()
                                      if k[0] == selected_abstract_tag and v >= min_frequency}
        else:
            filtered_abs_to_prim = {k: v for k, v in relationships['abstract_to_primary'].items() if v >= min_frequency}

    else:  # "전체 흐름 (추상→1차→2차)"
        # 추상 태그 필터 적용
        if selected_abstract_tag != "전체":
            # 다중 선택 처리
            if isinstance(selected_abstract_tag, list):
                # 선택된 추상 태그들과 연결된 관계만 필터링
                for (abs_tag, prim_tag), count in relationships['abstract_to_primary'].items():
                    if abs_tag in selected_abstract_tag and count >= min_frequency:
                        filtered_abs_to_prim[(abs_tag, prim_tag)] = count
            else:
                # 단일 선택 (이전 호환성)
                for (abs_tag, prim_tag), count in relationships['abstract_to_primary'].items():
                    if abs_tag == selected_abstract_tag and count >= min_frequency:
                        filtered_abs_to_prim[(abs_tag, prim_tag)] = count

            # 필터링된 1차 태그들과 연결된 2차 태그 관계 찾기
            connected_primary_tags = set(prim_tag for (abs_tag, prim_tag) in filtered_abs_to_prim.keys())
            for (prim_tag, sec_tag), count in relationships['primary_to_secondary'].items():
                if prim_tag in connected_primary_tags and count >= min_frequency:
                    filtered_prim_to_sec[(prim_tag, sec_tag)] = count
        else:
            # 전체 보기: 최소 빈도만 적용
            filtered_abs_to_prim = {k: v for k, v in relationships['abstract_to_primary'].items() if v >= min_frequency}
            filtered_prim_to_sec = {k: v for k, v in relationships['primary_to_secondary'].items() if v >= min_frequency}

    # 실제 사용되는 노드만 추출
    used_abstract_tags = set()
    used_primary_tags = set()
    used_secondary_tags = set()

    for (abs_tag, prim_tag) in filtered_abs_to_prim.keys():
        used_abstract_tags.add(abs_tag)
        used_primary_tags.add(prim_tag)

    for (prim_tag, sec_tag) in filtered_prim_to_sec.keys():
        used_primary_tags.add(prim_tag)
        used_secondary_tags.add(sec_tag)

    # 노드를 빈도순으로 정렬
    # 노드 생성
    all_nodes = []
    node_colors = []

    # 추상 태그 (빈도순 정렬)
    if used_abstract_tags:
        abstract_nodes = sort_by_frequency(used_abstract_tags, filtered_abs_to_prim, is_source=True)
    else:
        abstract_nodes = []
    all_nodes.extend([f"추상: {tag}" for tag in abstract_nodes])
    node_colors.extend(['#1f77b4'] * len(abstract_nodes))

    # 1차 태그 (빈도순 정렬)
    if used_primary_tags:
        # 1차 태그는 추상→1차 관계와 1차→2차 관계 둘 다 고려
        primary_freq = {}
        # 추상→1차에서 target으로서의 빈도
        for (abs_tag, prim_tag), count in filtered_abs_to_prim.items():
            if prim_tag in used_primary_tags:
                primary_freq[prim_tag] = primary_freq.get(prim_tag, 0) + count
        # 1차→2차에서 source로서의 빈도
        for (prim_tag, sec_tag), count in filtered_prim_to_sec.items():
            if prim_tag in used_primary_tags:
                primary_freq[prim_tag] = primary_freq.get(prim_tag, 0) + count

        primary_nodes = sorted(used_primary_tags, key=lambda x: primary_freq.get(x, 0), reverse=True)
    else:
        primary_nodes = []
    all_nodes.extend([f"1차: {tag}" for tag in primary_nodes])
    node_colors.extend(['#2ca02c'] * len(primary_nodes))

    # 2차 태그 (빈도순 정렬)
    if used_secondary_tags:
        secondary_nodes = sort_by_frequency(used_secondary_tags, filtered_prim_to_sec, is_source=False)
    else:
        secondary_nodes = []
    all_nodes.extend([f"2차: {tag}" for tag in secondary_nodes])
    node_colors.extend(['#ff7f0e'] * len(secondary_nodes))

    if not all_nodes:
        st.warning(f"선택된 조건에 맞는 태그 관계가 없습니다. (관계타입: {relationship_type}, 최소빈도: {min_frequency})")
        return

    # 노드 인덱스 맵핑
    node_dict = {node: idx for idx, node in enumerate(all_nodes)}

    def get_frequency_color(frequency, all_frequencies, link_type="abs_to_prim"):
        """빈도 분위수에 따른 색상 반환"""
        if not all_frequencies:
            return 'rgba(128, 128, 128, 0.6)'  # 기본 회색

        # 분위수 계산
        q25 = np.percentile(all_frequencies, 25)
        q50 = np.percentile(all_frequencies, 50)
        q75 = np.percentile(all_frequencies, 75)

        # 색상 팔레트 (추상→1차, 1차→2차별로 다른 색상)
        if link_type == "abs_to_prim":
            colors = {
                'Q1': 'rgba(255, 182, 193, 0.7)',  # 연한 핑크 (하위 25%)
                'Q2': 'rgba(255, 105, 180, 0.7)',  # 핫핑크 (25-50%)
                'Q3': 'rgba(220, 20, 60, 0.7)',    # 크림슨 (50-75%)
                'Q4': 'rgba(139, 0, 0, 0.8)'       # 다크레드 (상위 25%)
            }
        else:  # prim_to_sec
            colors = {
                'Q1': 'rgba(173, 216, 230, 0.7)',  # 연한 파랑 (하위 25%)
                'Q2': 'rgba(100, 149, 237, 0.7)',  # 코른플라워 블루 (25-50%)
                'Q3': 'rgba(65, 105, 225, 0.7)',   # 로얄 블루 (50-75%)
                'Q4': 'rgba(25, 25, 112, 0.8)'     # 미드나잇 블루 (상위 25%)
            }

        # 분위수에 따른 색상 결정
        if frequency <= q25:
            return colors['Q1']
        elif frequency <= q50:
            return colors['Q2']
        elif frequency <= q75:
            return colors['Q3']
        else:
            return colors['Q4']

    # 모든 빈도 값 수집 (분위수 계산용)
    abs_to_prim_frequencies = list(filtered_abs_to_prim.values())
    prim_to_sec_frequencies = list(filtered_prim_to_sec.values())

    # 링크 생성
    source = []
    target = []
    value = []
    link_colors = []

    # 추상 → 1차 링크
    for (abs_tag, prim_tag), count in filtered_abs_to_prim.items():
        source.append(node_dict[f"추상: {abs_tag}"])
        target.append(node_dict[f"1차: {prim_tag}"])
        value.append(count)
        color = get_frequency_color(count, abs_to_prim_frequencies, "abs_to_prim")
        link_colors.append(color)

    # 1차 → 2차 링크
    for (prim_tag, sec_tag), count in filtered_prim_to_sec.items():
        source.append(node_dict[f"1차: {prim_tag}"])
        target.append(node_dict[f"2차: {sec_tag}"])
        value.append(count)
        color = get_frequency_color(count, prim_to_sec_frequencies, "prim_to_sec")
        link_colors.append(color)

    # Sankey 다이어그램 생성
    if relationship_type == "1차→2차만":
        title_text = f"태그 관계도: 1차 → 2차 ({selected_primary_tag})" if selected_primary_tag != "전체" else "태그 관계도: 1차 → 2차"
    elif relationship_type == "추상→1차만":
        title_text = f"태그 관계도: 추상 → 1차 ({selected_abstract_tag})" if selected_abstract_tag != "전체" else "태그 관계도: 추상 → 1차"
    else:
        title_text = f"태그 관계도: 전체 흐름 ({selected_abstract_tag})" if selected_abstract_tag != "전체" else "태그 관계도: 전체 흐름"

    # 노드 위치 계산 (관계 타입에 따라)
    node_x = []
    node_y = []

    if relationship_type == "1차→2차만":
        # 1차 태그들 (X=0.01, 왼쪽)
        primary_count = len(primary_nodes)
        for i in range(primary_count):
            node_x.append(0.01)
            node_y.append(0.1 + (0.8 * i / max(1, primary_count - 1)) if primary_count > 1 else 0.5)

        # 2차 태그들 (X=0.99, 오른쪽)
        secondary_count = len(secondary_nodes)
        for i in range(secondary_count):
            node_x.append(0.99)
            node_y.append(0.1 + (0.8 * i / max(1, secondary_count - 1)) if secondary_count > 1 else 0.5)

    elif relationship_type == "추상→1차만":
        # 추상 태그들 (X=0.01, 왼쪽)
        abstract_count = len(abstract_nodes)
        for i in range(abstract_count):
            node_x.append(0.01)
            node_y.append(0.1 + (0.8 * i / max(1, abstract_count - 1)) if abstract_count > 1 else 0.5)

        # 1차 태그들 (X=0.99, 오른쪽)
        primary_count = len(primary_nodes)
        for i in range(primary_count):
            node_x.append(0.99)
            node_y.append(0.1 + (0.8 * i / max(1, primary_count - 1)) if primary_count > 1 else 0.5)

    else:  # "전체 흐름 (추상→1차→2차)"
        # 추상 태그들 (X=0.01, 왼쪽 열)
        abstract_count = len(abstract_nodes)
        for i in range(abstract_count):
            node_x.append(0.01)
            node_y.append(0.1 + (0.8 * i / max(1, abstract_count - 1)) if abstract_count > 1 else 0.5)

        # 1차 태그들 (X=0.5, 중간 열)
        primary_count = len(primary_nodes)
        for i in range(primary_count):
            node_x.append(0.5)
            node_y.append(0.1 + (0.8 * i / max(1, primary_count - 1)) if primary_count > 1 else 0.5)

        # 2차 태그들 (X=0.99, 오른쪽 열)
        secondary_count = len(secondary_nodes)
        for i in range(secondary_count):
            node_x.append(0.99)
            node_y.append(0.1 + (0.8 * i / max(1, secondary_count - 1)) if secondary_count > 1 else 0.5)

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_nodes,
            color=node_colors,
            x=node_x,
            y=node_y
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors
        )
    )])

    fig.update_layout(
        title_text=title_text,
        font_size=12,
        height=800
    )

    st.plotly_chart(fig, use_container_width=True)

    # 통계 정보 표시
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("추상 태그", len(relationships['abstract_tags']))

    with col2:
        st.metric("1차 태그", len(relationships['primary_tags']))

    with col3:
        st.metric("2차 태그", len(relationships['secondary_tags']))

    # 상위 관계 표시
    st.subheader("🔗 주요 태그 관계")

    # 추상→1차 상위 관계
    if relationships['abstract_to_primary']:
        st.write("**추상 → 1차 태그 (상위 10개)**")
        abs_to_prim_sorted = sorted(relationships['abstract_to_primary'].items(),
                                  key=lambda x: x[1], reverse=True)[:10]

        for (abs_tag, prim_tag), count in abs_to_prim_sorted:
            st.write(f"• {abs_tag} → {prim_tag}: {count}회")

    # 1차→2차 상위 관계
    if relationships['primary_to_secondary']:
        st.write("**1차 → 2차 태그 (상위 10개)**")
        prim_to_sec_sorted = sorted(relationships['primary_to_secondary'].items(),
                                  key=lambda x: x[1], reverse=True)[:10]

        for (prim_tag, sec_tag), count in prim_to_sec_sorted:
            st.write(f"• {prim_tag} → {sec_tag}: {count}회")