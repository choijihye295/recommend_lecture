import streamlit as st
import requests
import json
from typing import List, Dict

# 페이지 설정
st.set_page_config(
    page_title="강의 추천 시스템",
    page_icon="🎓",
    layout="wide"
)

# 스타일 설정
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .course-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

def display_course_info(course):
    """강의 정보를 표시하는 함수"""
    st.markdown("---")
    st.markdown(f"### {course['subject_name']}")
    
    # 기본 정보
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**담당교수:** {course['professor']}")
        st.markdown(f"**학과:** {course['major']}")
        st.markdown(f"**이수구분:** {course['course_type']}")
    
    with col2:
        if course['professor_phone']:
            st.markdown(f"**연락처:** {course['professor_phone']}")
        if course['professor_email']:
            st.markdown(f"**이메일:** {course['professor_email']}")
        if course['office']:
            st.markdown(f"**연구실:** {course['office']}")
    
    # 수업목표
    if course.get('course_objective'):
        st.markdown("#### 📚 수업목표")
        st.markdown(course['course_objective'])
    
    # 상세 정보
    if course['consultation_time'] or course['classroom'] or course['schedule']:
        st.markdown("#### 📝 상세 정보")
        if course['consultation_time']:
            st.markdown(f"**상담가능시간:** {course['consultation_time']}")
        if course['classroom']:
            st.markdown(f"**강의실:** {course['classroom']}")
        if course['schedule']:
            st.markdown(f"**요일/시간:** {course['schedule']}")
    
    # 전체 내용 표시 (접을 수 있는 섹션)
    with st.expander("전체 강의 정보 보기"):
        st.json(course['content'])

# 제목
st.title("🎓 강의 추천 시스템")

# 사이드바
with st.sidebar:
    st.header("💡 사용 방법")
    st.markdown("""
    1. 질문을 입력하세요
    2. '추천 받기' 버튼을 클릭하세요
    3. 추천 강의 목록을 확인하세요
    
    **예시 질문:**
    - 3학년인데 AI 관련 수업 추천해줘
    - 화학공학과 전공 과목 추천해줘
    - 공과대학 1학년 필수 과목 알려줘
    - OOO 교수님의 강의 정보 알려줘
    """)

# 메인 영역
# 질문 입력
query = st.text_area(
    "질문을 입력하세요",
    placeholder="예: 3학년인데 AI 관련 수업 추천해줘",
    height=100
)

# 추천 버튼
if st.button("추천 받기", type="primary"):
    if not query.strip():
        st.warning("질문을 입력해주세요.")
    else:
        with st.spinner("추천 강의를 생성하는 중..."):
            try:
                # API 요청
                api_url = "http://localhost:8001/api/recommend"
                #api_url = "https://recommend-lecture.onrender.com/api/recommend"
                #api_url = "https://recommend-lecture-qfo0.onrender.com/api/recommend"
                st.info(f"API 서버에 요청 중... ({api_url})")
                
                response = requests.post(
                    api_url,
                    json={"question": query, "chat_history": []},
                    timeout=60  # 타임아웃 설정 늘림
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 답변 표시
                    st.markdown("### 💬 추천 결과")
                    st.write(data["answer"])
                    
                    # 추천 강의 표시 > 삭제

                else:
                    st.error(f"API 요청 실패 (상태 코드: {response.status_code})")
                    st.error(f"오류 메시지: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("API 서버에 연결할 수 없습니다. API 서버가 실행 중인지 확인해주세요.")
                st.info("API 서버를 실행하려면: python api.py")
            except requests.exceptions.Timeout:
                st.error("API 요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
                st.error("상세 오류 정보:")
                st.exception(e)

# 푸터
st.markdown("---")
st.markdown("### 📝 참고사항")
st.markdown("""
- 추천 결과는 현재 데이터베이스에 있는 강의 정보를 기반으로 생성됩니다.
- 더 정확한 추천을 위해 구체적인 질문을 해주세요.
- 추천 결과는 참고용이며, 실제 수강 신청 시에는 학과 사무실에 문의하세요.
""") 