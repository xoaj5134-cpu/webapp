import io
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

#===========================================
# 기본 설정
#===========================================
st.set_page_config(page_title="고등학생 MBTI 검사", layout="wide")

# 세션 초기화
if "page" not in st.session_state:
    st.session_state.page = "test"
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = {}

#===========================================
# 1) 원본 mbti.csv 로딩 & 변환
#===========================================
@st.cache_data
def load_and_convert(csv_path="mbti.csv"):

    # CSV 읽기 (한글 인코딩 자동 처리)
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except:
        df = pd.read_csv(csv_path, encoding="cp949")
    
    # 불필요한 unnamed 컬럼 제거
    df = df.loc[:, ~df.columns.str.contains("Unnamed")]

    # 변환된 문항 리스트 저장
    records = []
    id_counter = 1

    pairs = [
        ("EI", "E", "I"),
        ("SN", "S", "N"),
        ("TF", "T", "F"),
        ("JP", "J", "P"),
    ]

    for _, row in df.iterrows():
        for dim, a_col, b_col in pairs:
            a_text = str(row[a_col]).strip()
            b_text = str(row[b_col]).strip()

            # 빈 셀이면 문항 생략
            if a_text == "nan" or b_text == "nan":
                continue

            records.append({
                "id": id_counter,
                "dimension_pair": dim,
                "question": f"{id_counter}번 문항",
                "option_a_text": a_text,
                "option_a_code": a_col,
                "option_b_text": b_text,
                "option_b_code": b_col,
            })
            id_counter += 1

    return pd.DataFrame(records)

df = load_and_convert("mbti.csv")
st.session_state.questions = df


#===========================================
# 2) 오른쪽 메뉴 UI
#===========================================
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
    if st.button("가이드"):
        st.session_state.page = "guide"
    if st.button("앱 정보"):
        st.session_state.page = "info"


#===========================================
# MBTI 계산 함수
#===========================================
def compute_mbti(df, answers):
    scores = {"E":0,"I":0,"S":0,"N":0,"T":0,"F":0,"J":0,"P":0}

    for _, row in df.iterrows():
        qid = row["id"]
        if qid in answers:
            scores[answers[qid]] += 1

    mbti = ""
    mbti += "E" if scores["E"] >= scores["I"] else "I"
    mbti += "S" if scores["S"] >= scores["N"] else "N"
    mbti += "T" if scores["T"] >= scores["F"] else "F"
    mbti += "J" if scores["J"] >= scores["P"] else "P"

    return mbti, scores


#===========================================
# 3) 검사 화면 (문항 하나씩 제시)
#===========================================
with col_left:

    if st.session_state.page == "test":
        st.header("📘 MBTI 진로 성향 검사")

        idx = st.session_state.idx
        questions = st.session_state.questions

        if idx < len(questions):
            row = questions.iloc[idx]

            st.subheader(f"{row['id']}번 문항")

            choice = st.radio(
                "",
                [row["option_a_text"], row["option_b_text"]],
                key=f"q_{row['id']}"
            )

            if st.button("다음 문항 ➜"):
                # 선택 기록
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


    #===========================================
    # 4) 결과 페이지
    #===========================================
    elif st.session_state.page == "result":
        st.header("📊 MBTI 검사 결과")

        mbti_type, scores = compute_mbti(df, st.session_state.answers)

        st.success(f"당신의 MBTI 유형은 **{mbti_type}** 입니다.")

        st.write("세부 점수:")
        st.write(scores)


    #===========================================
    # 5) 가이드
    #===========================================
    elif st.session_state.page == "guide":
        st.header("📘 MBTI 해석 가이드")
        st.write("각 유형 설명을 여기에 추가하면 됩니다.")


    #===========================================
    # 6) 정보 페이지
    #===========================================
    elif st.session_state.page == "info":
        st.header("ℹ️ 앱 정보")
        st.write("고등학생 진로 MBTI 검사 앱")
