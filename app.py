import streamlit as st
import fitz  # PyMuPDF
import os
import random
from datetime import date
from kiwipiepy import Kiwi
from collections import Counter
import math

# --- 1. 페이지 설정 및 스타일 숨기기 ---
st.set_page_config(page_title="PLAVE 꼬맨틀", page_icon="💙")

# 상단 헤더, 하단 푸터(Created by...), 메뉴 버튼을 숨기는 CSS
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            #stDecoration {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. 데이터 학습 및 유사도 엔진 ---
@st.cache_resource
def prepare_plave_engine():
    kiwi = Kiwi()
    pdf_texts = ""
    # 저장소 내 모든 PDF 파일 읽기
    for filename in os.listdir('.'):
        if filename.endswith('.pdf'):
            try:
                doc = fitz.open(filename)
                for page in doc:
                    pdf_texts += page.get_text() + "\n"
            except:
                continue
    
    # 형태소 분석 및 명사 추출
    tokens = kiwi.tokenize(pdf_texts)
    words = [t.form for t in tokens if t.tag.startswith('N') or t.tag == 'SL']
    
    word_counts = Counter(words)
    return word_counts, words

def calculate_score(target, guess, all_words):
    if target == guess: return 100.0
    if guess not in all_words: return 0.0
    
    # 단어 간 거리 기반 유사도 계산
    indices_target = [i for i, x in enumerate(all_words) if x == target]
    indices_guess = [i for i, x in enumerate(all_words) if x == guess]
    
    if not indices_target or not indices_guess: return 0.0
    
    min_dist = float('inf')
    for t_idx in indices_target:
        for g_idx in indices_guess:
            dist = abs(t_idx - g_idx)
            if dist < min_dist: min_dist = dist
    
    # 로그 스케일을 이용한 점수화 (거리가 멀수록 감점)
    score = max(0, 100 - (math.log(min_dist + 1) * 12))
    return round(score, 2)

# --- 3. 메인 로직 ---
st.title("💙 플레이브 꼬맨틀")
st.write("아스테룸의 지식을 바탕으로 오늘의 단어를 맞춰보세요!")

with st.spinner('데이터를 분석 중입니다...'):
    word_counts, all_words = prepare_plave_engine()

# 매일 바뀌는 정답 후보군
target_pool = ["예준", "노아", "밤비", "은호", "하민", "플레이브", "PLLI", "아스테룸", "카엘룸", "테라", "냥냥즈", "야타즈", "댕댕즈", "맏형즈", "쁜라인", "노스라이팅", "안바빠"]
valid_targets = [w for w in target_pool if w in word_counts]

# 오늘 날짜 기반 정답 고정
today_seed = date.today().strftime("%Y%m%d")
random.seed(today_seed)
target_word = random.choice(valid_targets)

if 'history' not in st.session_state:
    st.session_state.history = []

# 단어 입력창
with st.form(key='guess_form', clear_on_submit=True):
    user_input = st.text_input("단어를 입력하세요:").strip()
    submit = st.form_submit_button('확인')

if submit and user_input:
    # [제작자용 비밀 암호]
    if user_input == "아스테룸의빛":
        st.info(f"💡 [제작자 전용] 오늘의 정답은 **{target_word}** 입니다.")
    
    elif user_input == target_word:
        st.balloons()
        st.success(f"🎊 정답입니다! 오늘의 단어는 '{target_word}'였습니다!")
        if {"단어": user_input, "점수": 100.0} not in st.session_state.history:
            st.session_state.history.append({"단어": user_input, "점수": 100.0})
            
    elif user_input not in word_counts:
        st.warning(f"'{user_input}'은(는) AI가 모르는 단어입니다.")
        
    else:
        score = calculate_score(target_word, user_input, all_words)
        # 이미 입력한 단어가 아닐 때만 기록 추가
        if not any(h['단어'] == user_input for h in st.session_state.history):
            st.session_state.history.append({"단어": user_input, "점수": score})
        st.session_state.history.sort(key=lambda x: x['점수'], reverse=True)

# 추측 기록 표시
if st.session_state.history:
    st.write("---")
    st.write("### 추측 기록")
    for item in st.session_state.history:
        # 점수에 따른 색상 부여
        color = "blue" if item['점수'] >= 80 else "green" if item['점수'] >= 50 else "grey"
        st.write(f"- **{item['단어']}**: :{color}[{item['점수']}점]")