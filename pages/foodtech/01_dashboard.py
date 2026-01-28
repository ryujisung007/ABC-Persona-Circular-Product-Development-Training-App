import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO

# 페이지 설정
st.set_page_config(
    page_title="푸드테크 기업 대시보드",
    page_icon="🌟",
    layout="wide"
)

st.title("🥼 :green[푸드테크 기업 분석 대시보드]")

# 데이터 로딩
@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    return df

df = load_data()

# ✅ 중분류/소분류 필터
st.sidebar.header("📂 필터 선택")
mid_categories = df["중분류"].dropna().unique().tolist()
selected_mid = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(mid_categories))

filtered_df = df.copy()
if selected_mid != "전체":
    filtered_df = filtered_df[filtered_df["중분류"] == selected_mid]

sub_categories = filtered_df["소분류"].dropna().unique().tolist()
selected_sub = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(sub_categories))

if selected_sub != "전체":
    filtered_df = filtered_df[filtered_df["소분류"] == selected_sub]

# 📋 대표기술 클릭형 테이블
st.subheader(f"🔍 관련 기업 수: {len(filtered_df)}개")

# 선택된 대표기술 저장 변수
selected_tech = None

for idx, row in filtered_df.iterrows():
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button(f"🔎 {row['대표기술']}", key=f"tech_{idx}"):
            selected_tech = row['대표기술']
            selected_product = row.get('대표제품', '')
    with col2:
        st.markdown(f"**기업명:** {row['기업이름']}  \n**중분류:** {row['중분류']}  \n**소분류:** {row['소분류']}")

# ✅ 아래 영역: 기술 설명 + 이미지
if selected_tech:
    st.divider()
    st.markdown(f"### 📘 선택된 대표기술: **{selected_tech}**")

    col_left, col_right = st.columns(2)

    # 왼쪽: 기술 개요 (AI 기반 설명)
    with col_left:
        st.markdown("#### 💬 기술 개요")
        with st.spinner("AI 설명 생성 중..."):
            prompt = f"푸드테크 분야에서 '{selected_tech}' 기술이란 무엇이며 어떤 역할과 적용 예시가 있는지 간단히 설명해줘."
            try:
                from openai import OpenAI
                import openai
                openai.api_key = st.secrets["openai_api_key"]
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                explanation = response["choices"][0]["message"]["content"]
            except Exception as e:
                explanation = f"⚠️ 설명 생성 오류: {e}"
            st.markdown(explanation)

    # 오른쪽: 제품 이미지 검색
    with col_right:
        st.markdown("#### 🖼️ 대표제품 이미지 예시")
        if selected_product:
            query = f"{selected_tech} {selected_product} food product"
        else:
            query = f"{selected_tech} foodtech product"
        try:
            # DuckDuckGo 이미지 검색 API 유사 요청
            url = f"https://source.unsplash.com/600x400/?{query.replace(' ', ',')}"
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            st.image(img, caption=f"{selected_tech} 관련 이미지", use_column_width=True)
        except Exception as e:
            st.warning(f"이미지를 불러오지 못했습니다: {e}")
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
