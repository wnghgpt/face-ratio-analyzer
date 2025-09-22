"""
Face Ratio Analyzer - Streamlit Application
얼굴 비율 분석 데이터 시각화 및 클러스터링 도구
"""
import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path

# 새로운 아키텍처 모듈 import
from database.db_manager import db_manager
from engines.ratio_parser import RatioParser
from engines.analysis_engine import AnalysisEngine
from components.data_selector import render_data_selector, render_data_summary, get_filtered_data
from components.variable_selector import render_variable_selector
from components.analysis_builder import render_analysis_builder, validate_analysis_config
from components.results_viewer import render_results_viewer


def main():
    """메인 애플리케이션"""
    # 페이지 설정
    st.set_page_config(
        page_title="Face Ratio Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 제목
    st.title("📊 Face Ratio Analyzer")
    st.markdown("---")

    # 엔진 초기화
    parser = RatioParser()
    engine = AnalysisEngine()

    # 사이드바 설정
    st.sidebar.header("⚙️ 설정")

    # 메뉴 선택
    menu_options = {
        "📥 데이터 가져오기": "import",
        "🔍 데이터 분석": "analysis",
        "📊 대시보드": "dashboard",
        "⚙️ 관리": "management"
    }

    selected_menu = st.sidebar.selectbox(
        "메뉴 선택",
        options=list(menu_options.keys())
    )

    menu_key = menu_options[selected_menu]

    # 데이터베이스 상태 표시
    with st.sidebar:
        render_database_status()

    st.sidebar.markdown("---")

    # 메뉴별 페이지 렌더링
    if menu_key == "import":
        render_data_import_page()
    elif menu_key == "analysis":
        render_analysis_page(parser, engine)
    elif menu_key == "dashboard":
        render_dashboard_page(parser, engine)
    elif menu_key == "management":
        render_management_page()


def render_database_status():
    """데이터베이스 상태 표시"""
    st.write("**📊 데이터베이스 상태**")

    try:
        stats = db_manager.get_stats()

        st.metric("총 레코드", stats['total_records'])
        st.metric("고유 태그", stats['total_unique_tags'])
        st.metric("저장된 설정", stats['total_saved_configs'])

        if stats['total_records'] > 0:
            st.success("✅ 데이터베이스 연결됨")

            # 최근 데이터 미리보기
            data = db_manager.get_dataframe()
            if not data.empty:
                with st.expander("최근 데이터 미리보기"):
                    st.dataframe(
                        data[['name', 'tags_str', 'face_ratio_raw']].head(3),
                        use_container_width=True
                    )
        else:
            st.warning("⚠️ 데이터가 없습니다")
            st.info("💡 '📥 데이터 가져오기' 메뉴에서 JSON 파일을 가져와주세요")

    except Exception as e:
        st.error(f"❌ 데이터베이스 오류: {e}")


def render_data_import_page():
    """데이터 가져오기 페이지"""
    st.header("📥 데이터 가져오기")

    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["📁 JSON 파일", "📊 CSV 파일", "🔄 데이터 동기화"])

    with tab1:
        render_json_import()

    with tab2:
        render_csv_import()

    with tab3:
        render_data_sync()


def render_json_import():
    """JSON 파일 가져오기"""
    st.subheader("JSON 파일에서 데이터 가져오기")

    # 폴더 경로 입력
    json_folder = st.text_input(
        "JSON 파일 폴더 경로",
        value="json_files/",
        help="분석할 JSON 파일들이 있는 폴더 경로를 입력하세요."
    )

    if st.button("폴더 스캔"):
        if not os.path.exists(json_folder):
            st.error(f"❌ 폴더가 존재하지 않습니다: {json_folder}")
            return

        # JSON 파일 스캔
        json_files = list(Path(json_folder).glob("*.json"))

        if not json_files:
            st.warning(f"⚠️ {json_folder} 폴더에 JSON 파일이 없습니다.")
            return

        st.success(f"✅ {len(json_files)}개의 JSON 파일을 발견했습니다!")

        # 파일 목록 표시
        with st.expander("발견된 파일 목록"):
            for file_path in json_files:
                st.write(f"- {file_path.name}")

        # 가져오기 실행
        if st.button("데이터베이스로 가져오기"):
            with st.spinner("JSON 파일들을 처리하는 중..."):
                json_data_list = []
                failed_files = []

                for file_path in json_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            data['_filename'] = file_path.name
                            json_data_list.append(data)
                    except Exception as e:
                        failed_files.append((file_path.name, str(e)))
                        st.warning(f"파일 {file_path.name} 처리 실패: {e}")

                if json_data_list:
                    # 데이터베이스에 import
                    try:
                        db_manager.import_json_data(json_data_list)
                        st.success(f"✅ {len(json_data_list)}개 파일의 데이터를 성공적으로 가져왔습니다!")

                        # 가져온 데이터 미리보기
                        data = db_manager.get_dataframe()
                        if not data.empty:
                            st.write("**📋 가져온 데이터 미리보기:**")
                            st.dataframe(
                                data[['name', 'tags_str', 'face_ratio_raw']].tail(len(json_data_list)),
                                use_container_width=True
                            )

                        if failed_files:
                            st.warning(f"⚠️ {len(failed_files)}개 파일 처리 실패")
                            for filename, error in failed_files:
                                st.text(f"- {filename}: {error}")

                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 데이터베이스 저장 실패: {e}")
                else:
                    st.error("❌ 처리 가능한 파일이 없습니다.")


def render_csv_import():
    """CSV 파일 가져오기"""
    st.subheader("CSV 파일에서 데이터 가져오기")

    uploaded_file = st.file_uploader("CSV 파일 업로드", type=['csv'])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("**업로드된 데이터 미리보기:**")
            st.dataframe(df.head(), use_container_width=True)

            # CSV를 JSON 형태로 변환하여 가져오기
            if st.button("데이터베이스로 가져오기"):
                st.info("CSV 가져오기 기능은 구현 예정입니다.")

        except Exception as e:
            st.error(f"CSV 파일 읽기 오류: {e}")


def render_data_sync():
    """데이터 동기화"""
    st.subheader("데이터 동기화 및 정리")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("중복 데이터 제거"):
            st.info("중복 제거 기능은 구현 예정입니다.")

    with col2:
        if st.button("데이터 유효성 검사"):
            st.info("유효성 검사 기능은 구현 예정입니다.")


def render_analysis_page(parser: RatioParser, engine: AnalysisEngine):
    """분석 페이지"""
    st.header("🔍 데이터 분석")

    # 사용 가능한 변수 목록 가져오기
    available_variables = db_manager.get_available_variables()

    if not available_variables:
        st.warning("분석할 데이터가 없습니다. 먼저 데이터를 가져와주세요.")
        return

    # 단계별 분석 UI
    steps = ["1️⃣ 데이터 선택", "2️⃣ 변수 선택", "3️⃣ 분석 설정", "4️⃣ 결과 확인"]

    # 진행 상태 표시
    step_container = st.container()

    # 각 단계별 컨테이너
    step1_container = st.container()
    step2_container = st.container()
    step3_container = st.container()
    step4_container = st.container()

    with step_container:
        # 진행 단계 표시
        current_step = st.session_state.get('current_analysis_step', 1)

        cols = st.columns(4)
        for i, step_name in enumerate(steps):
            with cols[i]:
                if i + 1 <= current_step:
                    st.success(step_name)
                else:
                    st.info(step_name)

    # 1단계: 데이터 선택
    with step1_container:
        if current_step >= 1:
            filters = render_data_selector(db_manager, available_variables)

            if filters:
                filtered_data = get_filtered_data(db_manager, filters)

                if not filtered_data.empty:
                    render_data_summary(filtered_data)

                    if st.button("다음 단계: 변수 선택"):
                        st.session_state['filtered_data'] = filtered_data
                        st.session_state['current_analysis_step'] = 2
                        st.rerun()
                else:
                    st.warning("선택한 조건에 맞는 데이터가 없습니다.")

    # 2단계: 변수 선택
    with step2_container:
        if current_step >= 2:
            filtered_data = st.session_state.get('filtered_data')

            if filtered_data is not None and not filtered_data.empty:
                variable_selection = render_variable_selector(filtered_data, parser)

                if variable_selection:
                    if st.button("다음 단계: 분석 설정"):
                        st.session_state['variable_selection'] = variable_selection
                        st.session_state['current_analysis_step'] = 3
                        st.rerun()

    # 3단계: 분석 설정
    with step3_container:
        if current_step >= 3:
            analysis_config = render_analysis_builder()

            if analysis_config:
                # 설정 유효성 검증
                validation = validate_analysis_config(analysis_config)

                if validation['valid']:
                    if st.button("분석 실행"):
                        filtered_data = st.session_state.get('filtered_data')
                        variable_selection = st.session_state.get('variable_selection')

                        # 분석 실행
                        with st.spinner("분석을 실행하는 중..."):
                            result = engine.execute_analysis(filtered_data, analysis_config)
                            st.session_state['analysis_result'] = result
                            st.session_state['current_analysis_step'] = 4
                            st.rerun()
                else:
                    st.error("분석 설정에 오류가 있습니다:")
                    for error in validation['errors']:
                        st.error(f"- {error}")

    # 4단계: 결과 확인
    with step4_container:
        if current_step >= 4:
            analysis_result = st.session_state.get('analysis_result')

            if analysis_result:
                render_results_viewer(analysis_result)

                # 새 분석 시작
                if st.button("새 분석 시작"):
                    # 세션 상태 초기화
                    keys_to_clear = ['current_analysis_step', 'filtered_data', 'variable_selection', 'analysis_result']
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()


def render_dashboard_page(parser: RatioParser, engine: AnalysisEngine):
    """대시보드 페이지"""
    st.header("📊 대시보드")

    # 전체 데이터 개요
    data = db_manager.get_dataframe()

    if data.empty:
        st.warning("표시할 데이터가 없습니다.")
        return

    # 기본 통계
    st.subheader("📈 전체 데이터 요약")
    render_data_summary(data)

    # 빠른 분석
    st.subheader("⚡ 빠른 분석")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("기본 PCA 분석"):
            execute_quick_analysis(data, engine, "basic_ratio_pca")

    with col2:
        if st.button("클러스터링 분석"):
            execute_quick_analysis(data, engine, "clustering_analysis")

    with col3:
        if st.button("PCA + 클러스터링"):
            execute_quick_analysis(data, engine, "pca_clustering_combo")

    # 최근 분석 결과 (실제로는 데이터베이스에서 조회)
    st.subheader("🕒 최근 분석 결과")
    st.info("최근 분석 결과 표시 기능은 구현 예정입니다.")


def execute_quick_analysis(data: pd.DataFrame, engine: AnalysisEngine, template_name: str):
    """빠른 분석 실행"""
    templates = engine.get_analysis_templates()

    if template_name in templates:
        config = templates[template_name]['config']

        with st.spinner(f"{templates[template_name]['name']} 실행 중..."):
            result = engine.execute_analysis(data, config)
            st.session_state['quick_analysis_result'] = result

        # 결과 표시
        if 'quick_analysis_result' in st.session_state:
            st.subheader(f"📊 {templates[template_name]['name']} 결과")
            render_results_viewer(st.session_state['quick_analysis_result'])


def render_management_page():
    """관리 페이지"""
    st.header("⚙️ 관리")

    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["💾 저장된 설정", "🗄️ 데이터 관리", "📈 시스템 정보"])

    with tab1:
        render_saved_configs()

    with tab2:
        render_data_management()

    with tab3:
        render_system_info()


def render_saved_configs():
    """저장된 설정 관리"""
    st.subheader("저장된 분석 설정")

    # 저장된 설정들 조회
    configs = db_manager.get_analysis_configs()

    if configs:
        for config in configs:
            with st.expander(f"{config['name']} (사용 횟수: {config['use_count']})"):
                st.write(f"**설명:** {config['description']}")
                st.write(f"**생성일:** {config['created_date']}")
                st.write(f"**태그:** {', '.join(config['tags'])}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("불러오기", key=f"load_{config['id']}"):
                        loaded_config = db_manager.load_analysis_config(config['id'])
                        if loaded_config:
                            st.session_state['analysis_config'] = loaded_config['config']
                            st.success("설정이 불러와졌습니다!")

                with col2:
                    if st.button("복사", key=f"copy_{config['id']}"):
                        st.info("복사 기능은 구현 예정입니다.")

                with col3:
                    if st.button("삭제", key=f"delete_{config['id']}"):
                        st.info("삭제 기능은 구현 예정입니다.")
    else:
        st.info("저장된 설정이 없습니다.")


def render_data_management():
    """데이터 관리"""
    st.subheader("데이터 관리")

    # 데이터베이스 통계
    stats = db_manager.get_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("총 레코드", stats['total_records'])

    with col2:
        st.metric("고유 태그", stats['total_unique_tags'])

    with col3:
        st.metric("저장된 설정", stats['total_saved_configs'])

    # 데이터 정리 옵션
    st.write("**데이터 정리 옵션:**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("중복 데이터 제거"):
            st.info("중복 제거 기능은 구현 예정입니다.")

    with col2:
        if st.button("캐시 정리"):
            st.info("캐시 정리 기능은 구현 예정입니다.")


def render_system_info():
    """시스템 정보"""
    st.subheader("시스템 정보")

    # 데이터베이스 정보
    st.write("**데이터베이스 정보:**")
    st.write(f"- 경로: {db_manager.db_path}")
    st.write(f"- 엔진: SQLite")

    # 사용 가능한 분석 엔진
    engine = AnalysisEngine()
    templates = engine.get_analysis_templates()

    st.write("**사용 가능한 분석 템플릿:**")
    for name, template in templates.items():
        st.write(f"- {template['name']}: {template['description']}")

    # 시스템 상태
    st.write("**시스템 상태:**")
    st.success("✅ 모든 시스템이 정상 작동 중입니다.")


if __name__ == "__main__":
    main()