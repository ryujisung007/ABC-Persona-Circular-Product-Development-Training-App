# app.py (v4.0) - ABC 페르소나 + FoodTech 앱 선택 실행 구조
import streamlit as st
import os
import importlib.util

# 기본 설정
st.set_page_config(page_title="🧪 식품개발 멀티앱", layout="wide")
st.title("🥼 식품개발 멀티앱 플랫폼 v4.0")

# 앱 목록 정의
apps = {
    "🔁 ABC 페르소나 순환 개발": "abc_persona_main",
    "🥣 FoodTech 대시보드": "pages.foodtech.01_dashboard",
    "🔍 FoodTech 기술/제품 추천": "pages.foodtech.02_recommendation",
    "📊 FoodTech 요약 리포트": "pages.foodtech.03_summary"
}

# 앱 선택
selection = st.sidebar.selectbox("📂 실행할 앱 선택", list(apps.keys()))

# 선택된 모듈 import 및 실행
def run_selected_app(module_path):
    spec = importlib.util.find_spec(module_path)
    if spec is None:
        st.error(f"❌ '{module_path}' 모듈을 찾을 수 없습니다.")
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "main"):
        module.main()
    else:
        st.error(f"❌ '{module_path}'에는 main() 함수가 없습니다.")

# 앱 실행
if selection == "🔁 ABC 페르소나 순환 개발":
    # 기존 app.py 내용 직접 실행
    from abc_persona_main import main as abc_main
    abc_main()
else:
    run_selected_app(apps[selection])
# 기존 코드 그대로 유지하되 맨 아래만 수정

def run():
    main()

# 기존 if __name__ == "__main__": main() 제거
