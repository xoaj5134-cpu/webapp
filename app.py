import io
import os
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
# 1) mbti.csv 로딩 (clean_mbti 형식)
# =========================================
@st.cache_data
def load_mbti(csv_path: str = "mbti.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="cp949")

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
            "현재 파일이 clean_mbti 템플릿과 같은 구조인지 확인해 주세요."
        )

    df["id"] = df["id"].astype(int)
    df["question"] = df["question"].astype(str)
    df.loc[df["question"].isin(["nan", "", "None"]), "question"] = df["id"].apply(
        lambda x: f"{x}번 문항"
    )
    return df


df = load_mbti()


# =========================================
# 2) mbti_end.xlsx 로딩 (type, bullet 두 컬럼)
# =========================================
@st.cache_data
def load_mbti_profiles(xlsx_path: str = "mbti_end.xlsx") -> Dict[str, List[str]]:
    if not os.path.exists(xlsx_path):
        return {}

    profiles_df = pd.read_excel(xlsx_path)

    required_cols = ["type", "bullet"]
    missing = [c for c in required_cols if c not in profiles_df.columns]
    if missing:
        raise ValueError(
            f"mbti_end.xlsx에 다음 컬럼이 필요합니다: {missing}\n"
            "엑셀의 첫 행을 type, bullet 로 맞춰 주세요."
        )

    profiles: Dict[str, List[str]] = {}
    for _, row in profiles_df.iterrows():
        t = str(row["type"]).strip().upper()
        b = str(row["bullet"]).strip()
        if not t or t.lower() == "nan" or not b or b.lower() == "nan":
            continue
        profiles.setdefault(t, []).append(b)

    return profiles


MBTI_PROFILES = load_mbti_profiles()


# =========================================
# 3) 진로 추천 정보 (그대로 유지)
# =========================================
MBTI_RECOMMENDATIONS: Dict[str, Dict[str, List[str]]] = {
    "INTJ": {
        "majors": ["컴퓨터·소프트웨어공학", "데이터사이언스", "경영학", "정책학"],
        "careers": ["전략기획자", "데이터 분석가", "경영 컨설턴트", "프로덕트 매니저"],
    },
    "INFP": {
        "majors": ["심리학", "사회복지학", "국어국문·영문학", "콘텐츠·문화예술 관련 전공"],
        "careers": ["상담·복지 분야", "작가·에디터", "콘텐츠 기획자", "교육 관련 직무"],
    },
    # 필요하면 다른 유형도 추가 가능
}


# =========================================
# 4) MBTI 계산 & 결과 이미지 생성
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
# 5) 축별 자연어 설명 생성
# =========================================
def build_dimension_explanation(scores: Dict[str, int]) -> List[str]:
    lines: List[str] = []

    def one_pair(a_key, b_key, a_name, b_name, label):
        a = scores[a_key]
        b = scores[b_key]
        diff = a - b
        if diff > 0:
            lines.append(
                f"- **{label}** : {a_name}({a}) 점수가 {b_name}({b})보다 {abs(diff)}점 높아 "
                f"{a_name} 쪽 경향이 조금 더 강하게 나타납니다."
            )
        elif diff < 0:
            lines.append(
                f"- **{label}** : {b_name}({b}) 점수가 {a_name}({a})보다 {abs(diff)}점 높아 "
                f"{b_name} 쪽 경향이 조금 더 강하게 나타납니다."
            )
        else:
            lines.append(
                f"- **{label}** : 두 성향의 점수가 같아, 상황에 따라 {a_name}·{b_name} 성향이 모두 나타날 수 있습니다."
            )

    one_pair("E", "I", "외향(E)", "내향(I)", "에너지 방향 (E / I)")
    one_pair("S", "N", "감각(S)", "직관(N)", "정보 수용 방식 (S / N)")
    one_pair("T", "F", "사고(T)", "감정(F)", "판단 기준 (T / F)")
    one_pair("J", "P", "판단(J)", "인식(P)", "생활 방식 (J / P)")

    return lines


# =========================================
# 6) 오른쪽 메뉴 UI
# =========================================
with st.container():
    col_left, col_right = st.columns([4, 1])

with col_right:
    st.markdown("### 📌 메뉴")
    if st.button("검사하기", key="menu_test"):
        st.session_state.page = "test"
        st.session_state.idx = 0
        st.session_state.answers = {}
        st.rerun()

    if st.button("결과 보기", key="menu_result"):
        st.session_state.page = "result"
        st.rerun()

    if st.button("해석 가이드", key="menu_guide"):
        st.session_state.page = "guide"
        st.rerun()

    if st.button("앱 정보", key="menu_info"):
        st.session_state.page = "info"
        st.rerun()


# =========================================
# 7) 메인 화면 (왼쪽 영역)
# =========================================
with col_left:

    # 검사 페이지 – 한 문항씩
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

            if st.button("다음 문항 ➜", key=f"btn_next_{row['id']}"):
                if choice == row["option_a_text"]:
                    st.session_state.answers[row["id"]] = row["option_a_code"]
                else:
                    st.session_state.answers[row["id"]] = row["option_b_code"]

                st.session_state.idx += 1
                st.rerun()

        else:
            st.success("✔ 모든 문항을 완료했습니다.")
            if st.button("결과 보기", key="btn_complete_result"):
                st.session_state.page = "result"
                st.rerun()

    # 결과 페이지
    elif st.session_state.page == "result":
        st.header("📊 검사 결과")

        if not st.session_state.answers:
            st.warning("아직 검사 결과가 없습니다. 먼저 검사를 진행해 주세요.")
        else:
            mbti_type, scores = compute_mbti(df, st.session_state.answers)
            st.success(f"현재 성향에 기반한 MBTI 유형은 **{mbti_type}** 입니다.")

            # ① 축별 자연어 설명
            st.markdown("#### 검사 결과 해석")
            for line in build_dimension_explanation(scores):
                st.markdown(line)

            # ② 엑셀 기반 상세 불릿 설명 (메인 설명)
            bullets = MBTI_PROFILES.get(mbti_type, [])
            st.markdown("---")
            st.markdown("#### 성격·행동 특징 (검사지 기반)")

            if bullets:
                for b in bullets:
                    st.markdown(f"- {b}")
            else:
                st.info(
                    "이 유형에 대한 상세 불릿 설명은 아직 등록되지 않았습니다.\n"
                    "mbti_end.xlsx에 type, bullet 형식으로 내용을 추가해 주세요."
                )

            # ③ 진로 추천
            rec = MBTI_RECOMMENDATIONS.get(mbti_type, {})
            major_list = rec.get("majors", [])
            career_list = rec.get("careers", [])

            st.markdown("---")
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

            # ④ 점수 표
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

            # ⑤ PNG 다운로드
            st.markdown("---")
            st.markdown("### 📁 결과 요약 이미지(PNG) 다운로드")

            png_bytes = create_result_figure(mbti_type, scores, rec)
            st.download_button(
                label="결과 이미지 다운로드",
                data=png_bytes,
                file_name=f"mbti_result_{mbti_type}.png",
                mime="image/png",
            )

    # 해석 가이드
    elif st.session_state.page == "guide":
        st.header("📘 MBTI 결과 해석 가이드")
        st.write(
            "- MBTI는 현재 나의 전반적인 경향을 이해하기 위한 도구입니다.\n"
            "- 진로 선택 시에는 **흥미, 가치관, 능력, 환경** 등을 함께 고려해야 하며, MBTI는 참고 자료로 활용해 주세요.\n"
        )

    # 앱 정보
    elif st.session_state.page == "info":
        st.header("ℹ️ 앱 정보")
        st.write("고등학생 대상 진로 탐색용 MBTI 간이 검사 웹앱입니다.")
