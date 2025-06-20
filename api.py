from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import logging
import traceback
from vector_store import query_similar_courses
import json

from multi_chain_recommender import MultiChainRecommender #멀티체인

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#멀티체인
recommender = MultiChainRecommender()

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# VectorDB 로드
try:
    logger.info("VectorDB 로드 시작...")
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    logger.info("VectorDB 로드 완료")
except Exception as e:
    logger.error(f"VectorDB 로드 중 오류 발생: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# 대화 메모리 설정
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

# LLM 설정
try:
    logger.info("LLM 초기화 시작...")
    llm = ChatOpenAI(
        temperature=0.7,
        model_name="gpt-3.5-turbo",
        openai_api_key=OPENAI_API_KEY
    )
    logger.info("LLM 초기화 완료")
except Exception as e:
    logger.error(f"LLM 초기화 중 오류 발생: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# 커스텀 프롬프트 템플릿
template = """당신은 대학교 강의 추천 시스템입니다. 주어진 강의계획서 정보를 바탕으로 학생들에게 적절한 강의를 추천해주세요.

강의계획서 정보:
{context}

질문: {question}

답변할 때 다음 사항을 고려해주세요:
1. 강의계획서에 있는 구체적인 정보를 바탕으로 답변해주세요.
2. 교과목명, 담당교수, 이수구분, 학과/학년 등 기본 정보를 반드시 언급해주세요.
3. 수업 목표를 자세히 분석하여 강의의 핵심 내용과 특징을 설명해주세요.
4. 수업 목표에서 강의의 주요 학습 내용, 기대 효과, 실무 적용 가능성 등을 파악하여 설명해주세요.
5. 강의 내용, 평가 방법, 교재 정보 등 구체적인 정보를 포함해주세요.
6. 교수님의 이메일과 연락처가 있다면 함께 제공해주세요.
7. 질문과 관련성이 높은 강의만 추천해주세요. 관련성이 낮은 강의는 제외해주세요.
8. 강의 내용이 질문의 주제와 직접적으로 관련이 있는지 확인해주세요.
9. 모르는 정보에 대해서는 추측하지 말고, 있는 정보만 바탕으로 답변해주세요.
10. 수업 목표를 바탕으로 해당 강의가 질문자의 요구에 얼마나 부합하는지 설명해주세요.

답변:"""

QA_PROMPT = PromptTemplate(
    template=template,
    input_variables=["context", "question"]
)

# RAG 체인 설정
try:
    logger.info("RAG 체인 설정 시작...")
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 10,  # 검색 결과 수 증가
                "score_threshold": 0.7,  # 유사도 임계값 설정
                "filter": None  # 필요한 경우 필터 추가
            }
        ),
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT}
    )
    logger.info("RAG 체인 설정 완료")
except Exception as e:
    logger.error(f"RAG 체인 설정 중 오류 발생: {str(e)}")
    logger.error(traceback.format_exc())
    raise

class Query(BaseModel):
    question: str
    chat_history: list = []

@app.post("/api/recommend")
async def recommend_courses(query: Query):
    try:
        # 멀티체인 기반 추천 실행
        result = recommender.recommend(query.question)

        # 응답 분리
        answer = result.get("answer", "")
        source_docs = result.get("source_documents", [])

        # sources 정보 파싱 > 강의 정보 제공
        sources = []
        seen_subjects = set() #중복 강의 제거?

        for doc in source_docs:
            metadata = doc.metadata
            subject_name = metadata.get("subject_name", "")
            if subject_name in seen_subjects:
                continue
            seen_subjects.add(subject_name)

            sources.append({
                "subject_name": subject_name,
                "professor": metadata.get("professor", ""),
                "major": f"{metadata.get('major', '')} {metadata.get('year', '')}",
                "course_type": metadata.get("course_type", ""),
                "professor_phone": metadata.get("professor_phone", ""),
                "professor_email": metadata.get("professor_email", ""),
                "office": metadata.get("office", ""),
                "consultation_time": metadata.get("consultation_time", ""),
                "classroom": metadata.get("classroom", ""),
                "schedule": metadata.get("schedule", ""),
                "content": doc.page_content  # 원문 전체
            })

        return { #최종 응답구조
            "answer": answer,
            #"sources": sources
        }

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))  # Render가 지정한 PORT 사용
    uvicorn.run(app, host="0.0.0.0", port=port)