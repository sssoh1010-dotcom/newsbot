import streamlit as st
import feedparser
import datetime
import google.generativeai as genai
import urllib.parse

# [1] 페이지 설정
st.set_page_config(page_title="마이 리포트", layout="centered")

# [2] API 설정
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # 모델 이름을 정확한 버전(1.5 또는 2.0)으로 수정했습니다.
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API 설정 오류: {e}")

# [3] 세션 상태 초기화
for i in range(1, 5):
    if f'report_tab{i}' not in st.session_state: st.session_state[f'report_tab{i}'] = None
    if f'news_tab{i}' not in st.session_state: st.session_state[f'news_tab{i}'] = None

# [4] 뉴스 수집 함수
@st.cache_data(ttl=600)
def get_filtered_news(query, hours):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    if len(feed.entries) < 3:
        url = f"https://news.google.com/rss/search?q=경제+when:1d&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
    return feed.entries

# 뉴스 링크 표시용 공통 함수
def display_news_links(news_list):
    if news_list:
        with st.expander("🔗 분석 근거 뉴스 원문 보기"):
            for n in news_list[:7]:
                st.markdown(f"- [{n.title[:40]}...]({n.link})")

# [5] 메인 UI
st.title("📈마이 리포트")
tab1, tab2, tab3, tab4 = st.tabs(["종합", "테마", "심층", "⚡급상승"])

# --- 탭 1: 종합 리포트 ---
with tab1:
    st.subheader("🌐 글로벌 시장 통합 리포트")
    if st.button("🔥 실시간 리포트 생성", use_container_width=True, key="btn_t1"):
        with st.spinner("최신 시황 및 ETF 분석 중..."):
            news = get_filtered_news("국내 증시", 24)
            st.session_state.news_tab1 = news
            news_txt = "\n".join([f"- {n.title}" for n in news])
            
            # 파이썬이 직접 현재 날짜를 계산합니다 (예: 2026년 03월 16일)
            today_str = datetime.date.today().strftime("%Y년 %m월 %d일")
            
            # 모든 디테일을 살린 프롬프트
            prompt = f"""
            당신은 전문 투자 전략가입니다. 아래 지침에 따라 오늘({today_str})의 리포트를 작성하세요.
            반드시 제목을 "[ {today_str} 실시간 투자 전략 리포트 ]"로 시작하고, 2024년 같은 과거 날짜는 절대 언급하지 마세요.

            [작성 순서 및 지침]
            1. 시장 요약: 오늘 증시의 핵심 흐름과 주요 지수 변동을 3줄 내외로 요약.
            2. 주요 테마: 현재 뉴스에서 가장 뜨거운 강세 테마와 하락세인 약세 테마를 각각 1개씩 선정.
            3. 채권 및 안전자산: 금, 달러, 채권 등 안전자산의 동향을 2문장으로 요약.
            4. 🎯 AI 추천 ETF 종목 (중요): 
               - 앞선 시황을 바탕으로 지금 투자하기 좋은 국내 상장 ETF 3개를 엄선하세요.
               - 반드시 구체적인 종목명(예: KODEX 반도체, TIGER 미국나스닥100 등)을 포함할 것.
               - 각 종목별로 '왜 지금 사야 하는지' 근거를 1줄로 명확히 작성할 것.

            [참고 뉴스 데이터]
            {news_txt}
            """
            # AI에게 요청을 보냅니다.
            st.session_state.report_tab1 = model.generate_content(prompt).text
            
    if st.session_state.report_tab1:
        with st.container(border=True):
            st.markdown(st.session_state.report_tab1)
        display_news_links(st.session_state.news_tab1)
# --- 탭 2: 테마 분석 ---
with tab2:
    st.subheader("🔍 테마 심층 분석")
    selected = st.selectbox("테마 선택:", ["선택 안 함", "반도체", "2차전지", "AI 인프라", "바이오", "방산"])
    custom = st.text_input("직접 검색어 입력:")
    final_topic = custom if custom else (selected if selected != "선택 안 함" else None)
    
    if st.button("테마 분석 시작", use_container_width=True, key="btn_t2"):
        if final_topic:
            with st.spinner(f"'{final_topic}' 분석 중..."):
                news = get_filtered_news(final_topic, 24)
                st.session_state.news_tab2 = news
                news_txt = "\n".join([f"- {n.title}" for n in news])
                prompt = f"'{final_topic}' 테마 최신 이슈와 관련 한국 ETF 추천해줘.\n\n[데이터]\n{news_txt}"
                st.session_state.report_tab2 = model.generate_content(prompt).text
    if st.session_state.report_tab2:
        with st.container(border=True):
            st.markdown(st.session_state.report_tab2)
        display_news_links(st.session_state.news_tab2) # 근거 기사 버튼 복구

# --- 탭 3: 중요 뉴스 3선 (리포트 내 링크 포함) ---
with tab3:
    st.subheader("🕵️ 중요 뉴스 3선")
    if st.button("AI 뉴스 큐레이션", use_container_width=True, key="btn_t3"):
        with st.spinner("최적의 뉴스 선정 중..."):
            news = get_filtered_news("주식 시장 핵심 이슈", 24)
            if news:
                st.session_state.news_tab3 = news
                # AI에게 링크를 리포트에 직접 포함하라고 명시함
                news_txt = "\n".join([f"제목: {n.title} / 링크: {n.link}" for n in news])
                prompt = f"""
                아래 뉴스 중 가장 중요한 3개를 골라 리포트를 쓰세요.
                반드시 제목에 해당 뉴스 링크를 걸어주세요 (형식: [제목](링크)).
                그 아래에 '선정 이유'와 '핵심 요약'을 작성하세요.
                
                [데이터]
                {news_txt}
                """
                st.session_state.report_tab3 = model.generate_content(prompt).text
    if st.session_state.report_tab3:
        with st.container(border=True):
            st.markdown(st.session_state.report_tab3)
        display_news_links(st.session_state.news_tab3) # 전체 기사 리스트도 하단에 유지

# --- 탭 4: 급상승 ---
with tab4:
    st.subheader("⚡ 12시간 급상승 트렌드")
    if st.button("트렌드 즉시 분석", use_container_width=True, key="btn_t4"):
        with st.spinner("트렌드 파악 중..."):
            news = get_filtered_news("경제", 12)
            st.session_state.news_tab4 = news
            news_txt = "\n".join([f"- {n.title}" for n in news])
            st.session_state.report_tab4 = model.generate_content(f"최근 이슈 5개 선정 및 시사점 요약.\n\n{news_txt}").text
    if st.session_state.report_tab4:
        with st.container(border=True):
            st.markdown(st.session_state.report_tab4)
        display_news_links(st.session_state.news_tab4)