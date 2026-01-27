import streamlit as st
from openai import OpenAI, RateLimitError, AuthenticationError, BadRequestError
import time
import json

# 🧠 OpenAI 호출 함수
def call_openai_once(api_key: str, prompt: str, model: str = "gpt-4"):
    client = OpenAI(api_key=api_key)
    t0 = time.time()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        elapsed = time.time() - t0
        content = response.choices[0].message.content.strip()

        # JSON 파싱 시도
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"A": {}, "B": {}, "C": {}}

        return parsed, elapsed, None

    except RateLimitError as e:
        if "insufficient_quota" in str(e):
            return None, None, "❌ OpenAI 크레딧이 부족합니다. 결제 또는 예산을 확인하세요."
        return None, None, "⚠️ 요청이 너무 많아 일시적으로 제한되었습니다."

    except AuthenticationError:
        return None, None, "❌ 잘못된 API 키입니다."

    except BadRequestError as e:
        return None, None, f"❌ 잘못된 요청입니다: {e}"

    except Exception as e:
        return None, None, f"❌ 알 수 없는 오류: {e}"


# 📦 Prompt 생성 함수
def generate_prompt(info):
    return f"""
ABC 페르소나 순환 제품개발을 위한 신제품 제안서를 만들어줘. 아래 항목에 따라 결과는 JSON 형식으로 출력해줘.

🧾 조건 요약:
- 제품 목표: {info['goal']}
- 카테고리: {info['category']}
- 가격대: {info['price']}
- 출시시즌: {info['season']}
- 판매채널: {', '.join(info['channels'])}
- 출시일: {info['launch_date']}
- 시장환경: {info['market_env']}
- 트렌드 키워드: {', '.join(info['trends'])}

🎯 응답 형식(JSON) 예시:
{{
  "A": {{
    "name": "레몬버블",
    "slogan": "톡 쏘는 레몬, 건강한 하루",
    "functionality": "면역 강화 + 수분 보충"
  }},
  "B": {{
    "target_fit": "20-30대 여성 건강志向과 부합",
    "uniqueness": "국내산 오미자 기반 탄산음료",
    "marketability": "기존 헬스워터 시장과 차별화됨",
    "summary": "건강과 트렌드를 모두 잡은 여름 제품"
  }},
  "C": {{
    "오미자농축액": "5%",
    "레몬즙": "3%",
    "탄산수": "90%",
    "기타": "2%"
  }}
}}
"""


# 🚀 Streamlit 앱 메인 함수
def main():
    st.set_page_config(page_title="ABC 페르소나 순환 제품개발 앱", layout="wide")
    st.title("🥤 ABC 페르소나 순환 제품개발 앱")

    # ✅ 좌측 입력 폼
    with st.sidebar:
        st.header("제품 개발 목표")
        goal = st.selectbox("제품 목표", ["완전 신제품", "기존 제품 개선"])

        category = st.selectbox("제품 카테고리", ["탄산음료", "RTD 주스", "차음료", "기능성음료"])
        price = st.selectbox("희망 가격대", ["2000원 미만", "2000원 이상"])
        season = st.radio("출시 시즌", ["봄", "여름", "가을", "겨울"])

        channels = st.multiselect("판매 채널", ["편의점", "대형마트", "온라인몰", "카페", "마켓컬리"])

        st.markdown("### STEP 1. 시장 환경 입력")
        launch_date = st.text_input("출시 목표일 (YYYY-MM)", value="2026-05")
        market_env = st.text_area("시장 환경 요약", value="2030세대 증가, 고령화, 1인가구 확대 등")

        trends = st.multiselect("적용 트렌드", ["차별화", "뉴니스", "기능성", "저당", "친환경"])

        api_key = st.text_input("🔑 OpenAI API 키", type="password")

    # ✅ 실행 버튼
    if st.button("🚀 실행", type="primary", disabled=not api_key):
        inputs = {
            "goal": goal,
            "category": category,
            "price": price,
            "season": season,
            "channels": channels,
            "launch_date": launch_date,
            "market_env": market_env,
            "trends": trends,
        }

        prompt = generate_prompt(inputs)

        # ✅ 디버깅용 프롬프트 출력
        st.subheader("📄 생성된 Prompt")
        st.code(prompt, language="markdown")

        # ⏱ 호출
        with st.spinner("AI 생성 중..."):
            result, elapsed, err = call_openai_once(api_key, prompt)

        st.subheader("📊 대시보드")
        st.write(f"⏱ 소요시간: {elapsed:.2f}초")

        if err:
            st.error(err)
            st.stop()

        # ✅ 결과 출력
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### A. 제품 컨셉")
            if result["A"]:
                st.json(result["A"])
            else:
                st.warning("⚠️ 제품 컨셉 결과가 비어 있습니다.")

        with col2:
            st.markdown("### B. 마케팅 평가")
            if result["B"]:
                st.json(result["B"])
            else:
                st.warning("⚠️ 마케팅 평가 결과가 비어 있습니다.")

        with col3:
            st.markdown("### C. 제품 배합비")
            if result["C"]:
                st.json(result["C"])
            else:
                st.warning("⚠️ 제품 배합비 결과가 비어 있습니다.")


# ▶️ 실행
if __name__ == "__main__":
    main()
