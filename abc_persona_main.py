# abc_persona_main.py

import streamlit as st

def main():
    st.header("🔁 ABC 페르소나 기반 순환 개발")

    # 여기에 기존 기능 코드 삽입
    # 예시: 사용자 입력, 페르소나 설정, 시각화, 결과 출력 등

    st.markdown("이 앱은 ABC 페르소나를 기반으로 제품 개발 단계를 구성합니다.")

    # 예시 입력
    persona = st.selectbox("사용자 페르소나 선택", ["식품기획자", "패키징전문가", "소비자 리서처", "AI 연구원"], key="persona_selector")
    
    st.write(f"선택된 페르소나: **{persona}**")

    # 이후 분석 or 작업 모듈 호출
    # 예: if persona == ...: show_xxx()

    st.success("✅ ABC 페르소나 기능 정상 작동 중입니다.")

# 메인 앱 실행 (다른 곳에서 import 시 main() 함수만 실행됨)
