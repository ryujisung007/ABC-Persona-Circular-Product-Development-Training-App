import streamlit as st
import pandas as pd

# ==============================
# 데이터 로드
# ==============================
@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv", encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]  # 컬럼 공백 방지
    return df


# ==============================
# 메인 함수 (필수)
# ==============================
def main():
    st.set_page_config(
        page_title="FoodTech 기업 대시보드",
        layout="wide"
    )

    df = load_data()

    st.title("🥼 FoodTech 기업 분석 대시보드")
    st.markdown("중분류 → 소분류 → 대표기술 흐름으로 탐색합니다.")

    # ==============================
    # CSS (레이아웃 전용)
    # ==============================
    st.markdown("""
    <style>
    .panel-wrap {
        display: flex;
        gap: 20px;
        margin-top: 20px;
    }
    .left-panel {
        width: 48%;
        border: 2px solid #cfe2f3;
        border-radius: 10px;
        padding: 20px;
        background-color: #f8fbff;
    }
    .right-panel {
        width: 48%;
        border: 2px solid #fde2cf;
        border-radius: 10px;
        padding: 20px;
        background-color: #fff8f2;
    }
    .panel-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .placeholder {
        color: #888;
        font-size: 14px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

    # ==============================
    # 사이드바 필터
    # ==============================
    st.sidebar.header("🔍 기업 필터")

    mid = st.sidebar.selectbox(
        "중분류",
        ["전체"] + sorted(df["중분류"].dropna().unique().tolist()),
        key="mid_filter"
    )

    if mid != "전체":
        df = df[df["중분류"] == mid]

    sub = st.sidebar.selectbox(
        "소분류",
        ["전체"] + sorted(df["소분류"].dropna().unique().tolist()),
        key="sub_filter"
    )

    if sub != "전체":
        df = df[df["소분류"] == sub]

    # ==============================
    # 대표기술 선택 (클릭 대체 UX)
    # ==============================
    st.subheader("🧪 대표기술 선택")

    tech_list = sorted(df["대표기술"].dropna().unique().tolist())

    selected_tech = st.selectbox(
        "대표기술을 선택하세요",
        ["선택 안 함"] + tech_list,
        key="tech_select"
    )

    # ==============================
    # 테이블 출력
    # ==============================
    st.subheader(f"📋 기업 리스트 ({len(df)}개)")
    st.dataframe(
        df[["기업이름", "중분류", "소분류", "대표기술", "대표제품"]],
        use_container_width=True
    )

    # ==============================
    # 하단 패널 (AI / 이미지 자리)
    # ==============================
    st.markdown("---")

    st.markdown("<div class='panel-wrap'>", unsafe_allow_html=True)

    # 왼쪽: AI 기술 개요
    st.markdown("<div class='left-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>🤖 기술 개요 (AI 영역)</div>", unsafe_allow_html=True)

    if selected_tech == "선택 안 함":
        st.markdown(
            "<div class='placeholder'>대표기술을 선택하면<br>AI가 기술 개요를 설명합니다.</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(f"""
        <strong>{selected_tech}</strong><br><br>
        (※ 현재는 UI 설계 단계입니다)<br>
        이후 이 영역에 OpenAI API를 연결하여<br>
        • 기술 정의<br>
        • 적용 식품 카테고리<br>
        • R&D 활용 포인트<br>
        를 자동 생성합니다.
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # 오른쪽: 이미지 영역
    st.markdown("<div class='right-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>🖼️ 관련 제품 이미지</div>", unsafe_allow_html=True)

    if selected_tech == "선택 안 함":
        st.markdown(
            "<div class='placeholder'>대표기술 선택 시<br>대표제품 기반 이미지가 표시됩니다.</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(f"""
        <strong>{selected_tech}</strong> 기반 제품 이미지 영역<br><br>
        (※ 현재는 UI 설계 단계)<br>
        이후 이 영역에<br>
        • 대표제품 텍스트 분석<br>
        • Google 이미지 / AI 이미지 생성<br>
        을 연결합니다.
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# 실행 엔트리
# ==============================
if __name__ == "__main__":
    main()
