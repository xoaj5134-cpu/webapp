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

if "page" not in st.session_state:
    st.session_state.page = "test"   # test / result / guide / info

if "idx" not in st.session_state:
    st.session_state.idx = 0   # 현재 문항 index

if "answers" not in st.session_state:
    st.session_state.answers = {}  # id -> code


#===========================================
# CSV 로딩 함수
#===========================================
@st.cache_data
def load_mbti(csv_path="clean_mbti.csv"):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    # question 항목에 번호 자동 생성 (nan 제거)
    df["question"] = df["id"].apply(lambda x: f"{x}번 문항")
    return df

df = load_mbti()


#===========================================
# 우측 메뉴 구현
#===========================================
with st.container():
    col_left, col_right = st.columns([4, 1])

with col_right:
    st.markdown("### 📌 메뉴")
    if st.button("검사하기"):
        st.session_state.page = "test"
        st.session_state.idx = 0
    if st.button("결과 보기"):
        st.session_state.page = "result"
    if st.button("해석 가이드"):
        st.session_state.page = "guide"
    if st.button("앱 정보"):
        st.session_state.page = "info"


#===========================================
# MBTI 계산
#===========================================
def compute_mbti(df, answers):
    scores = {"E":0,"I":0,"S":0,"N":0,"T":0,"F":0,"J":0,"P":0}

    for _, row in df.iterrows():
        qid = row["id"]
        if qid in answers:
            code = answers[qid]
            scores[code] += 1

    mbti = ""
    mbti += "E" if scores["E"] >= scores["I"] else "I"
    mbti += "S" if scores["S"] >= scores["N"] else "N"
    mbti += "T" if scores["T"] >= scores["F"] else "F"
    mbti += "J" if scores["J"] >= scores["P"] else "P"

    return mbti, scores


#===========================================
# 메인 로직
#===========================================

with col_left:

    #---------------------------------------
    # 1) 검사 페이지 (문항 한 개씩)
    #---------------------------------------
    if st.session_state.page == "test":

        st.header("📘 MBTI 진로 성향 검사 (한 문항씩 진행)")

        idx = st.session_state.idx

        if idx < len(df):
            row = df.iloc[idx]

            st.subheader(f"문항 {row['id']}")

            # 선택 UI
            choice = st.radio(
                "",
                [row["option_a_text"], row["option_b_text"]],
                key=f"q_{row['id']}"
            )

            # 다음 문항
            if st.button("다음 문항 ➜"):
                # 선택한 내용을 저장
                if choice == row["option_a_text"]:
                    st.session_state.answers[row["id"]] = row["option_a_code"]
                else:
                    st.session_state.answers[row["id"]] = row["option_b_code"]

                st.session_state.idx += 1

                # 화면 새로고침
                st.experimental_rerun()

        else:
            st.success("모든 문항을 완료했습니다!")
            if st.button("결과 확인하기"):
                st.session_state.page = "result"
                st.experimental_rerun()


    #---------------------------------------
    # 2) 결과 페이지
    #---------------------------------------
    elif st.session_state.page == "result":

        st.header("📊 검사 결과")

        mbti_type, scores = compute_mbti(df, st.session_state.answers)
        st.success(f"당신의 MBTI 유형은 **{mbti_type}** 입니다.")


    #---------------------------------------
    # 3) 가이드
    #---------------------------------------
    elif st.session_state.page == "guide":
        st.header("📘 해석 가이드")
        st.write("각 유형에 대한 설명을 여기에 추가하면 됩니다.")

    #---------------------------------------
    # 4) 정보
    #---------------------------------------
    elif st.session_state.page == "info":
        st.header("ℹ️ 앱 정보")
        st.write("고등학생 진로 MBTI 테스트 앱")
