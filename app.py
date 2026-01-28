# app.py - 드롭다운으로 서브앱 구동하는 메인 앱
import streamlit as st
from abc_persona_main import run as run_abc_persona

# Streamlit 설정
st.set_page_config(page_title="Multi Persona Apps", layout="wide")

# 앱 목록
apps = {
    "ABC Persona App": run_abc_persona,
    # 추후 다른 앱 추가 가능
    # "Other App": run_other_app
}

# 사이드바 앱 선택
st.sidebar.title("📂 실행할 앱 선택")
app_choice = st.sidebar.selectbox("앱을 선택하세요", list(apps.keys()))

# 선택한 앱 실행
selected_app = apps[app_choice]
selected_app()
