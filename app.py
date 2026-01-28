# app.py (v5.0) - 드롭다운으로 각 앱 실행

"""
DEFAULT CODING RULES
- Role: 20년 경력 시니어 풀스택 개발자
- Constraints: 외부 라이브러리 최소, 오류 처리 포함, 가독성 최우선
- Process: 전체 코드 먼저 금지 → 데이터 구조 설계부터 단계별 제안
- Output: 최종 단계에서만 전체 코드 출력
"""
import streamlit as st
import importlib

st.set_page_config(page_title="🧪 식품개발 멀티앱 플랫폼", layout="wide")
# 앱 이름과 경로 설정
apps = {
    "🔁 가상 페르소나 개발모드": "abc_persona_main",
    "🥣 FoodTech 대시보드": "pages.foodtech.01_dashboard",
    "🔍 FoodTech 기술/제품 추천": "pages.foodtech.02_recommendation",
    "📊 FoodTech 요약 리포트": "pages.foodtech.03_summary"
}

# 사이드바에서 앱 선택 (key 추가)
selection = st.sidebar.selectbox("📂 실행할 앱 선택", list(apps.keys()), key="app_selector")

# 선택된 모듈 import 후 실행
def run_selected_app(module_path):
    try:
        module = importlib.import_module(module_path)
        if hasattr(module, "main"):
            module.main()
        else:
            st.error(f"❌ '{module_path}'에는 main() 함수가 없습니다.")
    except Exception as e:
        st.error(f"❌ 앱 실행 중 오류 발생: {e}")

# 앱 실행
run_selected_app(apps[selection])
