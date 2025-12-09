import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="진로 성향 검사 (MBTI + Holland RIASEC)",
    layout="wide",
)

st.title("🎯 진로 성향 검사")
st.caption("Streamlit 기반 MBTI / Holland RIASEC 간이 검사 데모 웹앱")

st.sidebar.title("메뉴")
page = st.sidebar.radio("이동하기", ["검사하기", "결과 해석 가이드", "앱 설명"])


# -----------------------------
# 질문 데이터
# -----------------------------

MBTI_QUESTIONS = [
    {
        "dimension": "EI",
        "question": "어떤 상황이 더 편안한가요?",
        "choices": [
            {"code": "E", "label": "여러 사람과 함께 이야기 나누는 모임"},
            {"code": "I", "label": "혼자 조용히 휴식하는 시간"},
        ],
    },
    {
        "dimension": "EI",
        "question": "새로운 사람을 만나는 것에 대해 어떻게 느끼나요?",
        "choices": [
            {"code": "E", "label": "새로운 사람을 만나는 것이 설레고 즐겁다"},
            {"code": "I", "label": "조금 부담스럽고 익숙한 사람이 더 좋다"},
        ],
    },
    {
        "dimension": "SN",
        "question": "정보를 받아들일 때 더 믿음이 가는 것은?",
        "choices": [
            {"code": "S", "label": "눈앞에 보이는 사실, 구체적인 정보"},
            {"code": "N", "label": "직관적으로 떠오르는 아이디어나 가능성"},
        ],
    },
    {
        "dimension": "SN",
        "question": "새 프로젝트를 시작할 때 나는...",
        "choices": [
            {"code": "S", "label": "지금 당장 필요한 것부터 차근차근 해나간다"},
            {"code": "N", "label": "전체적인 그림과 미래 가능성을 먼저 그린다"},
        ],
    },
    {
        "dimension": "TF",
        "question": "결정을 내릴 때 더 중요한 것은?",
        "choices": [
            {"code": "T", "label": "논리와 객관적인 기준"},
            {"code": "F", "label": "사람들의 감정과 관계"},
        ],
    },
    {
        "dimension": "TF",
        "question": "친구의 고민을 들을 때 나는 주로...",
        "choices": [
            {"code": "T", "label": "문제의 원인과 해결책을 분석해서 말해준다"},
            {"code": "F", "label": "감정에 공감하고 정서적으로 지지해 준다"},
        ],
    },
    {
        "dimension": "JP",
        "question": "일정을 관리할 때 나는...",
        "choices": [
            {"code": "J", "label": "미리 계획을 세우고 그에 맞춰 움직이는 편이다"},
            {"code": "P", "label": "상황을 보면서 유연하게 결정하는 편이다"},
        ],
    },
    {
        "dimension": "JP",
        "question": "마감 기한이 다가올 때 나는...",
        "choices": [
            {"code": "J", "label": "미리미리 준비해서 여유 있게 끝낸다"},
            {"code": "P", "label": "압박감이 있어야 집중이 잘 된다"},
        ],
    },
]

RIASEC_QUESTIONS = [
    # R - 현실형 (Realistic)
    {"dimension": "R", "question": "손으로 무언가를 만들거나 수리하는 것이 좋다."},
    {"dimension": "R", "question": "야외에서 활동하거나 몸을 쓰는 일이 재미있다."},
    {"dimension": "R", "question": "기계나 도구를 다루는 것이 어렵지 않다."},
    # I - 탐구형 (Investigative)
    {"dimension": "I", "question": "새로운 지식이나 원리를 이해하는 것이 즐겁다."},
    {"dimension": "I", "question": "수학, 과학, 논리적인 문제 풀기를 좋아한다."},
    {"dimension": "I", "question": "궁금한 것이 있으면 깊이 파고드는 편이다."},
    # A - 예술형 (Artistic)
    {"dimension": "A", "question": "그림, 글쓰기, 음악 등으로 표현하는 것을 좋아한다."},
    {"dimension": "A", "question": "자유롭고 개성 있는 환경이 편하다."},
    {"dimension": "A", "question": "정해진 규칙보다 새로운 방식을 시도해보는 것이 좋다."},
    # S - 사회형 (Social)
    {"dimension": "S", "question": "사람들의 고민을 듣고 도와주는 것이 좋다."},
    {"dimension": "S", "question": "팀 활동이나 협업을 선호하는 편이다."},
    {"dimension": "S", "question": "다른 사람에게 무언가를 가르치거나 안내하는 것이 즐겁다."},
    # E - 진취형 (Enterprising)
    {"dimension": "E", "question": "사람들을 이끌거나 설득하는 것에 자신이 있다."},
    {"dimension": "E", "question": "목표를 정하고 성과를 내는 것이 중요하다."},
    {"dimension": "E", "question": "위험이 있더라도 도전해보는 편이다."},
    # C - 관습형 (Conventional)
    {"dimension": "C", "question": "정리정돈과 체계적인 정리를 잘하는 편이다."},
    {"dimension": "C", "question": "규칙과 절차가 명확한 환경이 편하다."},
    {"dimension": "C", "question": "숫자, 문서, 자료를 다루는 일을 잘할 수 있을 것 같다."},
]


MBTI_DESCRIPTIONS = {
    "INTJ": "전략적인 계획형 사색가. 장기적인 비전과 구조를 세우는 데 강함.",
    "INTP": "논리적인 사색가. 개념 분석과 아이디어 탐구를 좋아함.",
    "ENTJ": "결단력 있는 리더형. 목표 설정과 조직 운영에 강점.",
    "ENTP": "도전적인 아이디어맨. 새로운 가능성을 탐색하고 토론을 즐김.",
    "INFJ": "통찰력 있는 조언자. 사람과 가치를 중시하며 깊이 있는 관계를 선호.",
    "INFP": "이상주의적인 중재자. 가치와 의미를 중요하게 생각함.",
    "ENFJ": "사교적인 지도자. 사람을 이끌고 협력적인 분위기를 만드는 데 강함.",
    "ENFP": "열정적인 아이디어형. 다양한 사람과 가능성을 탐색하는 것을 좋아함.",
    "ISTJ": "책임감 있는 관리자. 규칙과 절차를 잘 지키고 꼼꼼함.",
    "ISFJ": "헌신적인 보호자. 주변 사람을 세심하게 돌보고 지원함.",
    "ESTJ": "실용적인 조직가. 일 처리와 운영을 체계적으로 관리.",
    "ESFJ": "친화적인 협력가. 조화를 중요하게 여기고 사람들을 연결함.",
    "ISTP": "실용적인 해결사. 손으로 해결하고 문제를 직접 다루는 것을 선호.",
    "ISFP": "감성적인 예술가. 현재의 경험과 감각을 소중히 여김.",
    "ESTP": "활동적인 모험가. 실전 경험과 즉흥적인 도전을 즐김.",
    "ESFP": "자유로운 분위기 메이커. 사람들과 어울리며 즐거움을 추구.",
}

RIASEC_DESCRIPTIONS = {
    "R": "현실형(Realistic) — 몸을 쓰는 활동, 기계, 도구, 야외 활동에 강점.",
    "I": "탐구형(Investigative) — 분석, 연구, 문제 해결, 과학적 사고에 강점.",
    "A": "예술형(Artistic) — 창의적 표현, 예술, 디자인, 자유로운 환경 선호.",
    "S": "사회형(Social) — 사람을 돕고 가르치고 상담하는 활동에 강점.",
    "E": "진취형(Enterprising) — 설득, 리더십, 경영, 도전적인 목표에 강점.",
    "C": "관습형(Conventional) — 구조화된 환경, 문서, 숫자, 정리 정돈에 강점.",
}


# -----------------------------
# 유틸 함수
# -----------------------------
def compute_mbti_type(answers):
    scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
    for q, selected_label in answers.items():
        # q: question dict
        for choice in q["choices"]:
            if choice["label"] == selected_label:
                scores[choice["code"]] += 1

    # 각 축별로 타입 결정
    e_or_i = "E" if scores["E"] >= scores["I"] else "I"
    s_or_n = "S" if scores["S"] >= scores["N"] else "N"
    t_or_f = "T" if scores["T"] >= scores["F"] else "F"
    j_or_p = "J" if scores["J"] >= scores["P"] else "P"

    mbti_type = e_or_i + s_or_n + t_or_f + j_or_p
    return mbti_type, scores


def compute_riasec_scores(answers):
    scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
    for q, value in answers.items():
        dim = q["dimension"]
        scores[dim] += value
    return scores


def get_top_riasec_codes(scores, top_n=3):
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_codes = [code for code, _ in sorted_items[:top_n]]
    return "".join(top_codes), sorted_items


def plot_riasec_radar(scores):
    df = pd.DataFrame(
        {
            "type": list(scores.keys()),
            "score": list(scores.values()),
        }
    )
    # 점수가 0일 수 있으니 최소 1로 보정(그래프가 너무 찌그러지는 것 방지)
    max_score = max(scores.values()) if scores else 1
    fig = px.line_polar(
        df,
        r="score",
        theta="type",
        line_close=True,
        range_r=[0, max_score + 2],
    )
    fig.update_traces(fill="toself")
    return fig


# -----------------------------
# 페이지: 검사하기
# -----------------------------
if page == "검사하기":
    st.subheader("📋 MBTI 성향 & Holland RIASEC 간이 검사")

    tab_mbti, tab_riasec = st.tabs(["MBTI 성향 검사", "Holland RIASEC 검사"])

    # ---------- MBTI ----------
    with tab_mbti:
        st.markdown("### MBTI 성향 간이 검사")
        st.write("각 질문에서 **더 나와 비슷한 쪽**을 선택해 주세요.")

        mbti_answers = {}
        with st.form("mbti_form"):
            for idx, q in enumerate(MBTI_QUESTIONS):
                labels = [c["label"] for c in q["choices"]]
                answer = st.radio(
                    f"{idx+1}. {q['question']}",
                    labels,
                    key=f"mbti_q_{idx}",
                )
                mbti_answers[q] = answer

            submitted_mbti = st.form_submit_button("MBTI 결과 보기")

        if submitted_mbti:
            mbti_type, mbti_scores = compute_mbti_type(mbti_answers)
            st.success(f"당신의 MBTI 경향 유형(간이 분석)은 **{mbti_type}** 입니다.")
            desc = MBTI_DESCRIPTIONS.get(
                mbti_type, "해당 유형에 대한 설명이 준비되지 않았습니다."
            )
            st.write(desc)

            st.markdown("#### 세부 성향 점수")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("E (외향)", mbti_scores["E"])
                st.metric("I (내향)", mbti_scores["I"])
            with col2:
                st.metric("S (감각)", mbti_scores["S"])
                st.metric("N (직관)", mbti_scores["N"])
            with col3:
                st.metric("T (사고)", mbti_scores["T"])
                st.metric("F (감정)", mbti_scores["F"])
            with col4:
                st.metric("J (판단)", mbti_scores["J"])
                st.metric("P (인식)", mbti_scores["P"])

            st.info(
                "※ 실제 공식 MBTI 검사가 아니며, 진로 탐색을 위한 간이 성향 체크용으로 참고해 주세요."
            )

    # ---------- RIASEC ----------
    with tab_riasec:
        st.markdown("### Holland RIASEC 진로 흥미 검사 (간이판)")
        st.write(
            "각 문항에 대해 **자신에게 얼마나 잘 맞는지** 선택해 주세요. "
            "`1 = 전혀 그렇지 않다` ~ `5 = 매우 그렇다`"
        )

        riasec_answers = {}
        with st.form("riasec_form"):
            for idx, q in enumerate(RIASEC_QUESTIONS):
                value = st.select_slider(
                    f"{idx+1}. {q['question']}",
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    key=f"riasec_q_{idx}",
                )
                riasec_answers[q] = value

            submitted_riasec = st.form_submit_button("RIASEC 결과 보기")

        if submitted_riasec:
            scores = compute_riasec_scores(riasec_answers)
            top_code, sorted_items = get_top_riasec_codes(scores)

            st.success(
                f"당신의 Holland RIASEC 상위 조합(간이 분석)은 **{top_code}** 입니다."
            )

            st.markdown("#### 유형별 점수")
            df_scores = pd.DataFrame(sorted_items, columns=["유형", "점수"])
            st.table(df_scores)

            st.markdown("#### 각 유형 간단 해석")
            for code, score in sorted_items:
                st.markdown(
                    f"- **{code}** (점수: {score}) – {RIASEC_DESCRIPTIONS.get(code, '')}"
                )

            st.markdown("#### 레이더 차트로 시각화")
            fig = plot_riasec_radar(scores)
            st.plotly_chart(fig, use_container_width=True)

            st.info(
                "※ RIASEC 코드는 진로 흥미 경향을 나타내며, 상위 2~3개 조합을 "
                "참고하여 전공/직업군 탐색에 활용할 수 있습니다."
            )

# -----------------------------
# 페이지: 결과 해석 가이드
# -----------------------------
elif page == "결과 해석 가이드":
    st.subheader("📘 결과 해석 가이드")

    st.markdown("### MBTI 축별 간단 정리")
    st.markdown(
        """
**E / I**  
- **E(외향)**: 사람들과 함께 있을 때 에너지 ↑  
- **I(내향)**: 혼자 있는 시간에서 에너지 ↑  

**S / N**  
- **S(감각)**: 현재, 사실, 실용적인 정보 중시  
- **N(직관)**: 가능성, 아이디어, 미래지향적 사고 중시  

**T / F**  
- **T(사고)**: 논리, 객관적 기준으로 판단  
- **F(감정)**: 사람, 관계, 가치 기준으로 판단  

**J / P**  
- **J(판단)**: 계획적, 마감과 일정 관리 선호  
- **P(인식)**: 유연하고 즉흥적, 상황에 따라 움직임
"""
    )

    st.markdown("---")
    st.markdown("### Holland RIASEC 유형 정리")
    for code in ["R", "I", "A", "S", "E", "C"]:
        st.markdown(f"- **{code}**: {RIASEC_DESCRIPTIONS[code]}")

    st.markdown(
        """
#### 진로 탐색에 활용하는 법 (예시)
- **RS** 조합: 보건 계열 실무, 스포츠 트레이너, 물리치료사 등  
- **IA** 조합: 연구직, 데이터 분석, UX 리서처, 기획/콘텐츠 제작 등  
- **SE** 조합: 교사, 상담사, 영업/마케팅, HR 등  
- **AC** 조합: 디자이너 + 운영/기획, 콘텐츠 + 데이터 비교등
"""
    )

# -----------------------------
# 페이지: 앱 설명
# -----------------------------
elif page == "앱 설명":
    st.subheader("ℹ️ 앱 설명")

    st.markdown(
        """
이 웹앱은 Streamlit을 활용한 **진로 탐색용 간이 검사 데모**입니다.

- MBTI 구조를 참고한 **성향 체크**  
- Holland **RIASEC 진로 흥미 유형** 간단 분석  
- 결과를 기반으로 추후 **전공 / 직업 추천 기능**을 추가할 수 있습니다.

실제 서비스에 적용하려면:

1. **검사 문항을 공식 문항 또는 전문가가 검토한 문항**으로 교체  
2. **결과에 따른 진로/전공/직업 매핑 DB**를 구축  
3. 학생/사용자별 결과 저장, 리포트 다운로드, 관리자 페이지 등을 추가할 수 있습니다.
"""
    )
