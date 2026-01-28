# app.py (v4.1) - 안정형 멀티앱 라우터
import streamlit as st
import importlib

st.set_page_config(
    page_title="🧪 식품개발 멀티앱",
    layout="wide"
)

st.title("🥼 식품개발 멀티앱 플랫폼 v4.1")

# 앱 목록 (모듈 경로만 관리)
APP_REGISTRY = {
    "🔁 ABC 페르소나 순환 개발": "abc_persona_main",
    "🥣 FoodTech 대시보드": "pages.foodtech.01_dashboard",
    "🔍 FoodTech 기술/제품 추천": "pages.foodtech.02_recommendation",
    "📊 FoodTech 요약 리포트": "pages.foodtech.03_summary",
}

# 사이드바
st.sidebar.title("📂 앱 선택")
selection = st.sidebar.selectbox("실행할 앱을 선택하세요", list(APP_REGISTRY.keys()))

# 앱 로딩 & 실행
module_path = APP_REGISTRY[selection]

try:
    module = importlib.import_module(module_path)

    if not hasattr(module, "main"):
        st.error(f"❌ {module_path}.py 에 main() 함수가 없습니다.")
    else:
        module.main()

except Exception as e:
    st.exception(e)
