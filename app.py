import io
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")  # GUI 없는 서버 환경용
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# =========================================
# 기본 설정 & 세션 초기값
# =========================================
st.set_page_config(page_title="고등학생 진로 MBTI 검사", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "test"   # test / result / guide / info
if "idx" not in st.session_state:
    st.session_state.idx = 0         # 현재 문항 index
if "answers" not in st.session_state:
    st.session_state.answers = {}    # id -> code(E/I/…)


# =========================================
# mbti.csv 로딩 함수 (clean_mbti 형식 그대로 사용)
#  - 필요한 컬럼:
#    id, dimension_pair, question,
#    option_a_text, option_a_code,
#    option_b_text, option_b_code
# =========================================
@st.cache_data
def load_mbti(csv_path: str = "mbti.csv") -> pd.DataFrame:
    # 인코딩 자동 처리
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="cp949")

    # 불필요한 Unnamed 컬럼 제거
    df = df.loc[:, ~df.columns.str.contains("Unnamed")]

    required = [
        "id",
        "dimension_pair",
        "question",
        "option_a_text",
        "option_a_code",
        "option_b_text",
        "option_b_code",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"mbti.csv에 다음 컬럼이 필요합니다: {missing}\n"
            "현재 파일이 내가 준 clean_mbti 템플릿과 같은 구조인지 확인해 주세요."
        )

    # id 정수형, question 비어있으면 'n번 문항'으로 채우기
    df["id"] = df["id"].astype(int)
    df["question"] = df["question"].astype(str)
    df.loc[df["question"].isin(["nan", "", "None"]), "question"] = df["id"].apply(
        lambda x: f"{x}번 문항"
    )
    return df


df = load_mbti()  # 전역에서 한 번 로딩


# =========================================
# MBTI 설명 & 진로 추천 (간단 버전)
# =========================================
MBTI_DESCRIPTIONS: Dict[str, str] = {
    "INTJ": "전략적·계획적인 성향으로, 구조화된 환경에서 장기적인 목표를 세우는 데 강점이 있습니다.",
    "INTP": "논리적·탐구적인 성향으로, 개념과 아이디어를 분석하고 깊이 있게 파고드는 것을 선호합니다.",
    "ENTJ": "목표 지향적 리더 유형으로, 조직을 이끌고 성과를 내는 데 강점이 있습니다.",
    "ENTP": "도전적이고 창의적인 성향으로, 새로운 방식과 아이디어를 실험하는 것을 좋아합니다.",
    "INFJ": "통찰력과 공감 능력이 높아, 사람과 가치 중심의 활동에 강점을 보이는 유형입니다.",
    "INFP": "이상과 가치가 분명하며, 의미 있는 일을 추구하는 이상주의적 성향입니다.",
    "ENFJ": "사람을 이끌고 돕는 데 강점이 있으며, 공동체 분위기를 살리는 지도자형입니다.",
    "ENFP": "열정적이고 아이디어가 많은 유형으로, 다양한 사람과 가능성을 연결하는 역할에 강점이 있습니다.",
    "ISTJ": "성실하고 책임감이 강하며, 규칙과 절차를 잘 지키는 실무형 유형입니다.",
    "ISFJ": "배려심 깊고 헌신적인 성향으로, 주변을 세심하게 돌보는 보호자형입니다.",
    "ESTJ": "실용적이고 조직적인 성향으로, 일과 사람을 효율적으로 관리하는 관리자형입니다.",
    "ESFJ": "협력적이고 친화적인 성향으로, 관계를 조율하고 팀워크를 이끄는 데 강점이 있습니다.",
    "ISTP": "문제 해결 중심의 현실적인 유형으로, 직접 다루고 고치는 활동에 강점을 보입니다.",
    "ISFP": "감수성이 풍부하고 현재 경험을 중요시하는 예술가형 성향입니다.",
    "ESTP": "활동적이고 현실 감각이 뛰어나며, 실전 경험을 통해 배우는 모험가형입니다.",
    "ESFP": "사교적이고 밝은 분위기를 만드는 유형으로, 사람들과 함께하는 활동을 즐깁니다.",
}

MBTI_RECOMMENDATIONS: Dict[str, Dict[str, List[str]]] = {
    "INTJ": {
        "majors": ["컴퓨터·소프트웨어공학", "데이터사이언스", "경영학", "정책학"],
        "careers": ["전략기획자", "데이터 분석가", "경영 컨설턴트", "프로덕트 매니저"],
    },
    "INFP": {
        "majors": ["심리학", "사회복지학", "국어국문·영문학", "콘텐츠·문화예술 관련 전공"],
        "careers": ["상담·복지 분야", "작가·에디터", "콘텐츠 기획자", "교육 관련 직무"],
    },
    # ... 필요하면 다른 유형도 추가 가능
}


# =========================================
# MBTI 계산 & 결과 이미지 생성
# =========================================
def compute_mbti(df_items: pd.DataFrame, answers: Dict[int, str]) -> Tuple[str, Dict[str, int]]:
    scores = {k: 0 for k in ["E", "I", "S", "N", "T", "F", "J", "P"]}

    for _, row in df_items.iterrows():
        qid = row["id"]
        code = answers.get(qid)
        if code in scores:
            scores[code] += 1

    e_or_i = "E" if scores["E"] >= scores["I"] else "I"
    s_or_n = "S" if scores["S"] >= scores["N"] else "N"
    t_or_f = "T" if scores["T"] >= scores["F"] else "F"
    j_or_p = "J" if scores["J"] >= scores["P"] else "P"

    mbti_type = e_or_i + s_or_n + t_or_f + j_or_p
    return mbti_type, scores


def create_result_figure(
    mbti_type: str,
    scores: Dict[str, int],
    recommendations: Dict[str, List[str]],
) -> bytes:
    plt.rcParams["font.family"] = plt.rcParams.get("font.family", "sans-serif")

    fig, ax = plt.subplots(figsize=(7, 10))
    fig.suptitle("고등학생 진로 MBTI 결과 요약", fontsize=16, fontweight="bold")

    fig.text(
        0.5,
        0.92,
        f"MBTI 유형: {mbti_type}",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
    )

    y_labels = ["E / I", "S / N", "T / F", "J / P"]
    front_scores = [scores["E"], scores["S"], scores["T"], scores["J"]]
    back_scores = [scores["I"], scores["N"], scores["F"], scores["P"]]

    ax.barh(
        [y + 0.15 for y in range(len(y_labels))],
        front_scores,
        height=0.3,
        label="앞 글자(E/S/T/J)",
    )
    ax.barh(
        [y - 0.15 for y in range(len(y_labels))],
        back_scores,
        height=0.3,
        label="뒷 글자(I/N/F/P)",
    )

    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("점수(문항 수)", fontsize=11)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    major_list = recommendations.get("majors", [])
    career_list = recommendations.get("careers", [])

    majors_text = "추천 전공 예시\n- " + "\n- ".join(major_list) if major_list else "추천 전공 데이터 없음"
    careers_text = "추천 직업군 예시\n- " + "\n- ".join(career_list) if career_list else "추천 직업군 데이터 없음"

    text = majors_text + "\n\n" + careers_text

    fig.text(
        0.02,
        0.02,
        "※ 본 결과는 참고용이며, 공식 심리검사를 대체하지 않습니다.",
        fontsize=8,
        color="gray",
    )
    fig.text(
        0.52,
        0.25,
        text,
        fontsize=10,
        va="top",
        bbox=dict(boxstyle="round", facecolor="#f5f5f5", alpha=0.9),
    )

    buf = io.BytesIO()
    fig.tight_layout(rect=[0, 0.05, 1, 0.9])
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# =========================================
# 오른쪽 메뉴 UI
# =========================================
with st.container():
    col_left, col_right = st.columns([4, 1])

with col_right:
    st.markdown("### 📌 메뉴")
    if st.button("검사하기"):
        st.session_state.page = "test"
        st.session_state.idx = 0
        st.session_state.answers = {}
    if st.button("결과 보기"):
        st.session_state.page = "result"
    if st.button("해석 가이드"):
        st.session_state.page = "guide"
    if st.button("앱 정보"):
        st.session_state.page = "info"


# =========================================
# 메인 화면 (왼쪽 영역)
# =========================================
with col_left:

    # 1) 검사 페이지 – 한 문항씩
    if st.session_state.page == "test":
        st.header("📘 MBTI 진로 성향 검사")

        idx = st.session_state.idx
        total = len(df)

        if idx < total:
            row = df.iloc[idx]

            st.progress((idx + 1) / total)
            st.subheader(f"{row['id']}번 문항")

            choice = st.radio(
                "",
                [row["option_a_text"], row["option_b_text"]],
                key=f"q_{row['id']}",
            )

            if st.button("다음 문항 ➜"):
                if choice == row["option_a_text"]:
                    st.session_state.answers[row["id"]] = row["option_a_code"]
                else:
                    st.session_state.answers[row["id"]] = row["option_b_code"]

                st.session_state.idx += 1
                st.experimental_rerun()

        else:
            st.success("✔ 모든 문항을 완료했습니다.")
            if st.button("결과 보기"):
                st.session_state.page = "result"
                st.experimental_rerun()

    # 2) 결과 페이지
    elif st.session_state.page == "result":
        st.header("📊 검사 결과")

        if not st.session_state.answers:
            st.warning("아직 검사 결과가 없습니다. 먼저 검사를 진행해 주세요.")
        else:
            mbti_type, scores = compute_mbti(df, st.session_state.answers)
            st.success(f"현재 성향에 기반한 MBTI 유형은 **{mbti_type}** 입니다.")

            desc = MBTI_DESCRIPTIONS.get(
                mbti_type, "해당 유형에 대한 설명 정보가 준비 중입니다."
            )
            st.markdown("#### 유형 설명")
            st.write(desc)

            rec = MBTI_RECOMMENDATIONS.get(mbti_type, {})
            major_list = rec.get("majors", [])
            career_list = rec.get("careers", [])

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 추천 전공 예시")
                if major_list:
                    for m in major_list:
                        st.markdown(f"- {m}")
                else:
                    st.write("전공 추천 정보가 준비 중입니다.")
            with c2:
                st.markdown("#### 추천 직업군 예시")
                if career_list:
                    for c in career_list:
                        st.markdown(f"- {c}")
                else:
                    st.write("직업군 추천 정보가 준비 중입니다.")

            st.markdown("---")
            st.markdown("### 세부 점수(축별 경향)")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("E (외향)", scores["E"])
                st.metric("I (내향)", scores["I"])
            with c2:
                st.metric("S (감각)", scores["S"])
                st.metric("N (직관)", scores["N"])
            with c3:
                st.metric("T (사고)", scores["T"])
                st.metric("F (감정)", scores["F"])
            with c4:
                st.metric("J (판단)", scores["J"])
                st.metric("P (인식)", scores["P"])

            st.markdown("---")
            st.markdown("### 📁 결과 요약 이미지(PNG) 다운로드")

            png_bytes = create_result_figure(mbti_type, scores, rec)
            st.download_button(
                label="결과 이미지 다운로드",
                data=png_bytes,
                file_name=f"mbti_result_{mbti_type}.png",
                mime="image/png",
            )

    # 3) 해석 가이드
    elif st.session_state.page == "guide":
        st.header("📘 MBTI 결과 해석 가이드")
        st.write(
            "- MBTI는 성격을 딱 잘라서 구분하기 위한 것이 아니라, **현재 나의 경향을 이해하기 위한 도구**입니다.\n"
            "- 진로 선택 시에는 **흥미, 가치관, 능력, 환경** 등을 함께 고려해야 하며, MBTI는 참고 자료로 활용해 주세요.\n"
        )

    # 4) 앱 정보
    elif st.session_state.page == "info":
        st.header("ℹ️ 앱 정보")
        st.write("고등학생 대상 진로 탐색용 MBTI 간이 검사 웹앱입니다.")
