import io
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")  # Streamlit Cloud 등 GUI 없는 환경에서 사용
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# =========================================
# 기본 설정
# =========================================
st.set_page_config(
    page_title="고등학생 진로 MBTI 검사",
    layout="wide",
)

st.title("🎓 고등학생 진로 MBTI 검사")
st.caption("학교·상담센터에서 활용 가능한 진로 탐색용 MBTI 간이 검사")

st.sidebar.title("메뉴")
page = st.sidebar.radio("페이지 이동", ["검사하기", "결과 해석 가이드", "앱 안내"])


# =========================================
# MBTI 문항 로딩
#   ▶ mbti.csv 형식(예시)
#   id,dimension_pair,question,option_a_text,option_a_code,option_b_text,option_b_code
#   1,EI,어떤 상황이 더 편안한가요?,여러 사람과 함께 이야기하는 모임,E,혼자 조용히 시간을 보내는 것,I
# =========================================

@st.cache_data
def load_mbti_items(csv_path: str = "mbti.csv") -> pd.DataFrame:
    """
    mbti.csv 파일을 읽어옵니다.
    - 기본적으로 Windows/Excel에서 저장된 한국어 CSV는 CP949 인코딩을 많이 사용합니다.
    """
    try:
        # 1차 시도: CP949 (한국어 Windows 환경에서 가장 흔함)
        df = pd.read_csv(csv_path, encoding="cp949")
    except UnicodeDecodeError:
        # 2차 시도: UTF-8 (혹시 UTF-8로 저장된 경우)
        df = pd.read_csv(csv_path, encoding="utf-8")

    required_cols = [
        "id",
        "dimension_pair",
        "question",
        "option_a_text",
        "option_a_code",
        "option_b_text",
        "option_b_code",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"mbti.csv에 다음 컬럼이 필요합니다: {missing}\n"
            "예시: id, dimension_pair, question, option_a_text, "
            "option_a_code, option_b_text, option_b_code"
        )
    return df


# =========================================
# MBTI 설명 및 진로 추천 데이터
# =========================================

MBTI_DESCRIPTIONS: Dict[str, str] = {
    "INTJ": "전략적이고 계획적인 성향으로, 장기적인 비전과 구조를 세우는 데 강점이 있습니다.",
    "INTP": "논리적이고 탐구적인 성향으로, 아이디어와 개념을 분석하는 것을 선호합니다.",
    "ENTJ": "목표 지향적이고 리더십이 강한 성향으로, 조직을 이끌고 성과를 내는 데 강점이 있습니다.",
    "ENTP": "도전적이고 창의적인 성향으로, 새로운 가능성을 탐색하고 토론을 즐깁니다.",
    "INFJ": "통찰력과 공감 능력이 높아, 사람과 가치 중심의 활동에 강점을 보입니다.",
    "INFP": "이상주의적이고 가치 지향적인 성향으로, 의미 있는 일을 추구하는 경향이 있습니다.",
    "ENFJ": "사람을 이끌고 돕는 데 강점이 있으며, 협력적인 분위기를 조성하는 데 능숙합니다.",
    "ENFP": "열정적이고 창의적인 성향으로, 다양한 사람과 아이디어를 연결하는 데 강점이 있습니다.",
    "ISTJ": "책임감이 강하고 체계적인 성향으로, 규칙과 절차를 잘 준수합니다.",
    "ISFJ": "성실하고 배려심이 깊은 성향으로, 주변을 세심하게 돌보는 데 강점이 있습니다.",
    "ESTJ": "실용적이고 조직적인 성향으로, 일 처리와 운영을 효율적으로 관리합니다.",
    "ESFJ": "친화적이고 협력적인 성향으로, 사람들 간의 조화를 중요하게 생각합니다.",
    "ISTP": "실제적인 문제 해결에 강점이 있으며, 손으로 직접 다루는 활동을 선호합니다.",
    "ISFP": "감수성이 풍부하며, 현재의 경험과 감각을 중요하게 여기는 성향입니다.",
    "ESTP": "활동적이고 현실 감각이 뛰어나며, 실전 경험을 통해 배우는 것을 선호합니다.",
    "ESFP": "사교적이고 밝은 성향으로, 주변 사람들과 즐거운 분위기를 만드는 데 강점이 있습니다.",
}

# 각 유형별(고등학생 기준) 전공·직업군 예시 추천
MBTI_RECOMMENDATIONS: Dict[str, Dict[str, List[str]]] = {
    "INTJ": {
        "majors": ["공학 계열(전기·전자, 컴퓨터)", "경영학", "데이터사이언스", "정책학"],
        "careers": ["전략기획자", "데이터 분석가", "경영 컨설턴트", "프로덕트 매니저"],
    },
    "INTP": {
        "majors": ["컴퓨터공학", "수학·통계", "물리학", "인공지능 관련 전공"],
        "careers": ["연구원", "소프트웨어 개발자", "데이터 사이언티스트", "기술 분석가"],
    },
    "ENTJ": {
        "majors": ["경영학", "경제학", "공학+경영(융합전공)", "국제학"],
        "careers": ["경영자·창업가", "프로젝트 매니저", "마케팅/영업 관리자", "공기업·공공기관 관리자"],
    },
    "ENTP": {
        "majors": ["경영·벤처창업", "미디어커뮤니케이션", "콘텐츠 기획 관련 전공", "디자인씽킹 관련 학제전공"],
        "careers": ["스타트업 창업", "기획자", "광고·마케팅 직무", "콘텐츠/프로덕트 플래너"],
    },
    "INFJ": {
        "majors": ["심리학", "교육학", "사회복지학", "인문·사회계열"],
        "careers": ["상담 교사", "심리상담사", "사회복지사", "비영리 기관 활동가"],
    },
    "INFP": {
        "majors": ["국어국문·영문학 등 문학계열", "심리학", "사회복지학", "예술·콘텐츠 관련 전공"],
        "careers": ["작가·에디터", "상담·복지 관련 직무", "콘텐츠 크리에이터", "교육 관련 직무"],
    },
    "ENFJ": {
        "majors": ["교육학", "심리·상담학", "인사·조직 관련 전공", "사회학"],
        "careers": ["교사", "HR/인사 담당자", "조직 개발 컨설턴트", "교육 기획자"],
    },
    "ENFP": {
        "majors": ["광고·홍보학", "미디어커뮤니케이션", "문화·예술경영", "콘텐츠 관련 전공"],
        "careers": ["광고·홍보 기획자", "MCN/콘텐츠 크리에이터", "이벤트·공연 기획자", "브랜드 매니저"],
    },
    "ISTJ": {
        "majors": ["회계·재무 관련 전공", "법학", "공기업 선호 전공", "공학계열"],
        "careers": ["공무원", "회계사·세무사", "품질관리·생산관리", "행정·사무직"],
    },
    "ISFJ": {
        "majors": ["간호·보건 계열", "교육학", "사회복지학", "유아교육·특수교육"],
        "careers": ["간호사", "교사", "사회복지사", "보건·복지 관련 공무원"],
    },
    "ESTJ": {
        "majors": ["경영학", "행정학", "산업공학", "유통·물류 관련 전공"],
        "careers": ["조직·현장 관리자", "공공기관·공기업", "프로젝트 매니저", "영업·유통 관리자"],
    },
    "ESFJ": {
        "majors": ["교육학", "간호·보건 계열", "호텔·관광경영", "사회복지학"],
        "careers": ["교사", "간호사", "서비스·관광 분야", "인사·조직 관리"],
    },
    "ISTP": {
        "majors": ["기계·자동차공학", "전기·전자공학", "정보보안·네트워크", "스포츠과학"],
        "careers": ["엔지니어", "정비·기술직", "정보보안 전문가", "스포츠 트레이너"],
    },
    "ISFP": {
        "majors": ["시각·실기 예술", "패션·디자인", "음악·공연예술", "유아·보육 관련 전공"],
        "careers": ["디자이너", "공연·예술 관련 직무", "보육교사", "플로리스트·공방 운영"],
    },
    "ESTP": {
        "majors": ["스포츠과학", "경영·마케팅", "호텔·관광", "경찰·소방 관련 전공"],
        "careers": ["스포츠 지도자", "세일즈·영업", "이벤트 기획", "경찰·소방"],
    },
    "ESFP": {
        "majors": ["공연예술·뮤지컬", "방송·연예 관련 전공", "관광·서비스 경영", "유아·아동학"],
        "careers": ["배우·공연자", "방송·엔터테인먼트", "서비스·관광 직무", "아동 관련 교육 직무"],
    },
}


# =========================================
# MBTI 계산 관련 함수
# =========================================

def compute_mbti_type_from_answers(
    df_items: pd.DataFrame, answer_codes: Dict[int, str]
) -> Tuple[str, Dict[str, int]]:
    """
    answer_codes: question id -> 선택된 코드(E/I/S/N/T/F/J/P 중 하나)
    """
    scores: Dict[str, int] = {k: 0 for k in ["E", "I", "S", "N", "T", "F", "J", "P"]}

    for _, row in df_items.iterrows():
        qid = row["id"]
        code = answer_codes.get(qid)
        if code in scores:
            scores[code] += 1

    # 각 축 결정
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
    """
    MBTI 결과를 요약한 PNG 이미지를 생성하여 bytes로 반환
    """
    # 폰트 설정(서버 환경에 따라 한글 폰트가 없을 수 있으나, 없는 경우에도 동작 자체는 합니다)
    plt.rcParams["font.family"] = plt.rcParams.get("font.family", "sans-serif")

    fig, ax = plt.subplots(figsize=(7, 10))

    fig.suptitle("고등학생 진로 MBTI 결과 요약", fontsize=16, fontweight="bold")

    # 상단 MBTI 타입 표시
    fig.text(
        0.5,
        0.92,
        f"MBTI 유형: {mbti_type}",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
    )

    # 축별 점수 바 차트
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

    # 우측에 텍스트 박스: 전공·직업 추천
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

    # 이미지를 메모리에 저장
    buf = io.BytesIO()
    fig.tight_layout(rect=[0, 0.05, 1, 0.9])
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# =========================================
# 페이지 1: 검사하기
# =========================================
if page == "검사하기":
    st.subheader("📋 MBTI 성향 검사")

    st.markdown(
        """
고등학생을 대상으로 한 **진로 탐색용 MBTI 성향 검사**입니다.  
각 문항에 대해, 현재 나에게 더 잘 맞는 선택지를 골라 주세요.

> ※ 본 검사는 학교·상담센터에서 참고용으로 활용하기 위한 간이 검사이며,  
>   정식 임상 도구가 아님을 안내드립니다.
"""
    )

    try:
        df_mbti = load_mbti_items()
    except Exception as e:
        st.error("⚠️ 문항 파일(mbti.csv)을 불러오는 과정에서 오류가 발생했습니다.")
        st.exception(e)
        st.stop()

    with st.form("mbti_form"):
        st.markdown("### 문항에 답변해 주세요")

        answer_codes: Dict[int, str] = {}

        for _, row in df_mbti.iterrows():
            qid = int(row["id"])
            question = str(row["question"])
            a_text = str(row["option_a_text"])
            b_text = str(row["option_b_text"])
            a_code = str(row["option_a_code"]).strip().upper()
            b_code = str(row["option_b_code"]).strip().upper()

            choice = st.radio(
                f"{qid}. {question}",
                [a_text, b_text],
                key=f"q_{qid}",
            )
            if choice == a_text:
                answer_codes[qid] = a_code
            else:
                answer_codes[qid] = b_code

        submitted = st.form_submit_button("검사 결과 확인")

    if submitted:
        if len(answer_codes) != len(df_mbti):
            st.warning("모든 문항에 응답해 주셔야 정확한 결과를 확인할 수 있습니다.")
        else:
            mbti_type, scores = compute_mbti_type_from_answers(df_mbti, answer_codes)
            st.success(f"검사 결과, 현재 성향에 기반한 MBTI 유형은 **{mbti_type}** 입니다.")

            # 설명
            desc = MBTI_DESCRIPTIONS.get(
                mbti_type,
                "해당 유형에 대한 기본 설명 정보가 아직 등록되어 있지 않습니다.",
            )
            st.markdown("#### 유형 설명")
            st.write(desc)

            # 진로 추천
            rec = MBTI_RECOMMENDATIONS.get(mbti_type, {})
            major_list = rec.get("majors", [])
            career_list = rec.get("careers", [])

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 추천 전공 예시")
                if major_list:
                    for m in major_list:
                        st.markdown(f"- {m}")
                else:
                    st.write("해당 유형에 대한 전공 추천 정보가 준비 중입니다.")

            with col2:
                st.markdown("#### 추천 직업군 예시")
                if career_list:
                    for c in career_list:
                        st.markdown(f"- {c}")
                else:
                    st.write("해당 유형에 대한 직업 추천 정보가 준비 중입니다.")

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

            st.info(
                "※ 점수 차이가 크지 않은 축은 상황에 따라 양쪽 성향이 모두 나타날 수 있습니다."
            )

            # PNG 결과 생성 및 다운로드 버튼
            st.markdown("---")
            st.markdown("### 📁 결과 이미지(PNG)로 저장하기")

            png_bytes = create_result_figure(mbti_type, scores, rec)
            st.download_button(
                label="결과 요약 이미지(PNG) 다운로드",
                data=png_bytes,
                file_name=f"mbti_result_{mbti_type}.png",
                mime="image/png",
            )


# =========================================
# 페이지 2: 결과 해석 가이드
# =========================================
elif page == "결과 해석 가이드":
    st.subheader("📘 결과 해석 가이드")

    st.markdown(
        """
MBTI 결과는 **성격 유형을 정확히 단정 짓기보다는, 현재 나의 경향을 이해하는 참고 자료**로 활용하는 것이 좋습니다.  
특히 고등학생의 경우 경험의 폭이 넓지 않기 때문에, 학교생활·동아리·가정·또래관계 등 여러 상황을 함께 고려해 해석해야 합니다.
"""
    )

    st.markdown("### 1. 각 축(E/I, S/N, T/F, J/P)의 의미")
    st.markdown(
        """
**E / I (에너지 방향)**  
- **E(외향)**: 사람들과 함께 있을 때 에너지를 얻는 편, 활동적·표현적  
- **I(내향)**: 혼자 있는 시간에서 에너지를 얻는 편, 사색적·조용한 환경 선호  

**S / N (정보를 받아들이는 방식)**  
- **S(감각)**: 현재의 사실, 구체적인 정보, 경험을 중시  
- **N(직관)**: 가능성, 아이디어, 미래의 방향성을 중시  

**T / F (판단 기준)**  
- **T(사고)**: 논리와 일관된 기준, 객관성을 중시  
- **F(감정)**: 관계와 감정, 사람에 미치는 영향을 중시  

**J / P (생활 방식)**  
- **J(판단형)**: 계획적, 마감과 일정 관리, 준비된 상태를 선호  
- **P(인식형)**: 유연하고 즉흥적, 상황을 보며 결정하는 편
"""
    )

    st.markdown("---")
    st.markdown("### 2. 진로 탐색 시 유의점")

    st.markdown(
        """
1. **MBTI만으로 진로를 결정하지 않습니다.**  
   - 흥미, 가치관, 능력, 환경, 가정 상황 등 다양한 요소가 함께 고려되어야 합니다.

2. **유형은 '고정된 운명'이 아니라 현재 경향을 설명하는 틀**입니다.  
   - 학년이 바뀌거나 경험이 쌓이면, 삶의 방식과 선호도 달라질 수 있습니다.

3. **같은 유형이라도 선택하는 진로는 매우 다양**합니다.  
   - 예: ENFP라도 공학 계열에서 창의성을 발휘하거나, INTP라도 예술/콘텐츠 분야에서 분석적 사고를 활용할 수 있습니다.

4. **검사 결과는 대화의 출발점**입니다.  
   - 담임교사, 진로 상담 선생님, 보호자와 함께 결과를 보며  
     ‘왜 이런 결과가 나왔는지’, ‘어떤 상황에서 나에게 더 맞는지’를 이야기해 보는 것이 중요합니다.
"""
    )

    st.markdown("---")
    st.markdown("### 3. 학교에서 활용 예시")

    st.markdown(
        """
- 학급 단위로 검사 후, **유형별 강점·유의점 안내 자료** 제공  
- 진로 포트폴리오에 검사 결과를 정리하고, **희망 전공·직업과 연결해서 작성**  
- 상담 시간에, **학습 습관·대인관계·진로 고민**과 함께 MBTI 결과를 참고 자료로 활용  
"""
    )


# =========================================
# 페이지 3: 앱 안내
# =========================================
elif page == "앱 안내":
    st.subheader("ℹ️ 앱 안내")

    st.markdown(
        """
이 웹앱은 **Streamlit**을 활용하여 제작된  
고등학생 대상 **진로 탐색용 MBTI 검사 도구(간이판)** 입니다.

#### 주요 특징
- 질문 문항은 `mbti.csv` 파일에서 관리하며, 학교/기관 상황에 맞게 수정 가능합니다.
- 검사 결과를 바탕으로 **전공·직업군 예시**를 함께 제시합니다.
- 검사 결과를 **PNG 이미지**로 다운로드하여,  
  진로 포트폴리오나 상담 기록에 첨부할 수 있습니다.

#### 활용 시 권장 사항
- 반드시 **“참고용 도구”**임을 안내하고,  
  공식 심리검사 또는 전문 상담을 대체하지 않는다는 점을 명시해 주세요.
- 필요에 따라, 학교의 진로부/상담부와 협의하여  
  **문항 내용 및 결과 해석 문구**를 조정하는 것을 권장드립니다.
"""
    )

    st.markdown(
        """
#### 기술 요소
- Python, Streamlit  
- Pandas를 활용한 CSV 문항 관리  
- Matplotlib(Agg backend)를 활용한 결과 요약 이미지 생성
"""
    )
