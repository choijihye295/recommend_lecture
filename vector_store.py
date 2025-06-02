from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_processor import Course, Syllabus
import json
import os
from dotenv import load_dotenv
import shutil

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 데이터베이스 설정
DATABASE_URL = "sqlite:///course_recommender.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# ChromaDB 설정
CHROMA_DB_DIR = "./chroma_db"
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

def get_vector_store():
    """VectorDB 인스턴스 반환"""
    return Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings
    )

def get_course_documents():
    """데이터베이스에서 강의 정보를 가져와 문서 형식으로 변환"""
    session = Session()
    try:
        courses = session.query(Course).all()
        documents = []

        for course in courses:
            # 기본 정보
            basic_info = json.loads(course.syllabus.basic_info)
            professor_info = json.loads(course.syllabus.professor_info)
            course_info = json.loads(course.syllabus.course_info)
            evaluation = json.loads(course.syllabus.evaluation)
            textbook_info = json.loads(course.syllabus.textbook_info)
            core_competencies = json.loads(course.syllabus.core_competencies)

            # 텍스트 생성 (JSON 구조 반영)
            text = f"""
            강의 기본 정보:
            - 교과목명: {course.subject_name}
            - 담당교수: {course.professor}
            - 이수구분: {course.course_type}
            - 학과/학년: {course.major} {course.year}
            - 분반: {course.class_number}
            - 학기: {course.semester}

            기본 정보:
            - 이메일: {basic_info.get('email', '')}
            - 연락처: {basic_info.get('phone', '')}
            - 수업목표: {basic_info.get('course_objective', '')}

            교수 정보:
            - 연구실: {professor_info.get('office', '')}
            - 상담가능시간: {professor_info.get('consultation_time', '')}

            강의 정보:
            - 강의실: {course_info.get('classroom', '')}
            - 요일/시간: {course_info.get('schedule', '')}

            교재 정보:
            - 주교재: {textbook_info.get('main_textbook', '')}
            - 참고자료: {textbook_info.get('reference', '')}

            """

            # 메타데이터 (None 값을 빈 문자열로 변환)
            metadata = {
                "subject_code": course.subject_code or "",
                "subject_name": course.subject_name or "",
                "class_number": course.class_number or "",
                "professor": course.professor or "",
                "college": course.college or "",
                "major": course.major or "",
                "course_type": course.course_type or "",
                "year": course.year or "",
                "semester": course.semester or "",
                "professor_email": basic_info.get('email', '') or "",
                "professor_phone": basic_info.get('phone', '') or "",
                "course_objective": basic_info.get('course_objective', '') or "",
                "office": professor_info.get('office', '') or "",
                "consultation_time": professor_info.get('consultation_time', '') or "",
                "classroom": course_info.get('classroom', '') or "",
                "schedule": course_info.get('schedule', '') or ""
            }

            documents.append({"text": text, "metadata": metadata})

        return documents
    finally:
        session.close()

def create_vector_store():
    #기존 chroma db 삭제
    if os.path.exists(CHROMA_DB_DIR):
        print("기존 Chroma DB가 존재합니다. 삭제 후 새로 생성합니다.")
        shutil.rmtree(CHROMA_DB_DIR)
    else:
        print("Chroma DB 디렉토리가 존재하지 않습니다. 새로 생성합니다.")

    """VectorDB 생성"""
    # 문서 가져오기
    documents = get_course_documents()
    
    # 텍스트 분할 (청크 크기를 500으로 감소)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,  # 청크 크기 감소 500 > 300
        chunk_overlap=100,  # 오버랩 감소
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    
    texts = []
    metadatas = []
    
    for doc in documents:
        if not doc["text"].strip():
            continue
        chunks = text_splitter.split_text(doc["text"])
        texts.extend(chunks)
        metadatas.extend([doc["metadata"]] * len(chunks))
    
    if not texts:
        print("임베딩할 텍스트가 없습니다. 데이터베이스에 데이터가 있는지 확인하세요.")
        return

    # 배치 크기 설정 (한 번에 처리할 텍스트 수)
    BATCH_SIZE = 20  # 배치 크기 감소
    
    # VectorDB 생성
    vectorstore = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=CHROMA_DB_DIR
    )
    
    vectorstore.persist()
    print("VectorDB 생성 완료")

def query_similar_courses(query_text, n_results=5):
    """유사한 강의 검색"""
    try:
        # VectorDB 인스턴스 가져오기
        vectorstore = get_vector_store()
        
        # 쿼리 실행 (검색 결과 수 증가)
        results = vectorstore.similarity_search_with_score(
            query=query_text,
            k=20  # 검색 결과 수 증가
        )
        
        # 결과 처리
        if results:
            # 중복 제거를 위한 set
            seen_subjects = set()
            formatted_results = []
            
            for doc, score in results:
                # 메타데이터에서 교과목명 가져오기
                metadata = doc.metadata
                subject_name = metadata.get("subject_name", "")
                
                # 이미 본 교과목이면 건너뛰기
                if subject_name in seen_subjects:
                    continue
                
                # 유사도 점수가 너무 낮으면 건너뛰기 (0.5 이상만 포함 > 0.8이상만 포함)
                if float(score) < 0.7:
                    continue
                
                # 결과 추가
                result = {
                    "content": doc.page_content,
                    "metadata": metadata,
                    "score": float(score)
                }
                formatted_results.append(json.dumps(result, ensure_ascii=False))
                seen_subjects.add(subject_name)
                
                # 원하는 수의 결과를 얻으면 중단
                if len(formatted_results) >= n_results:
                    break
            
            # 결과가 없으면 임계값을 더 낮춰서 재시도
            if not formatted_results:
                for doc, score in results:
                    metadata = doc.metadata
                    subject_name = metadata.get("subject_name", "")
                    
                    if subject_name in seen_subjects:
                        continue
                    
                    # 임계값을 0.3으로 낮춤 > 0.5
                    if float(score) < 0.5:
                        continue
                    
                    result = {
                        "content": doc.page_content,
                        "metadata": metadata,
                        "score": float(score)
                    }
                    formatted_results.append(json.dumps(result, ensure_ascii=False))
                    seen_subjects.add(subject_name)
                    
                    if len(formatted_results) >= n_results:
                        break
            
            return formatted_results
        return []
        
    except Exception as e:
        print(f"쿼리 실행 중 오류 발생: {str(e)}")
        return []

if __name__ == "__main__":
    create_vector_store() 