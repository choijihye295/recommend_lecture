# 강의계획서 크롤링 및 추천 시스템

이 프로젝트는 대학 강의계획서를 크롤링하고, 데이터베이스에 저장한 뒤, 강의 추천 및 검색 기능을 제공하는 시스템입니다.

## 주요 기능

- 강의계획서 JSON 데이터 파싱 및 DB 저장
- 강의 정보(교수명, 이메일, 강의유형 등) 추출
- 강의 추천 및 검색 API 제공
- 간단한 프론트엔드 제공

## 폴더/파일 구조

- `data_processor.py` : 강의계획서 JSON 파일을 파싱하여 DB에 저장하는 스크립트
- `vector_store.py` : 벡터 DB 관련 기능
- `api.py` / `app.py` : API 서버
- `check_data.py` : DB에 저장된 강의 정보 확인용 스크립트
- `frontend/` : 간단한 웹 프론트엔드
- `data/` : (git에는 포함되지 않음) 강의계획서 원본 데이터
- `.gitignore` : 불필요한 파일/폴더 제외 설정
- `transformer_question_classifier` : 질문 유형 분류
- `prompts.py` : 질문 유형에 따라 다른 프롬프트
- `multi_chain_recommender.py` : 질문 유형에 따른 프롬프트 선택해서 벡터DB에서 검색

## 설치 및 실행 방법

1. **필요 패키지 설치**
    ```bash
    pip install -r requirements.txt
    ```
    (requirements.txt가 없다면, 사용된 주요 패키지: `flask`, `sqlite3`, `pandas` 등)

2. **강의계획서 데이터 파싱 및 DB 저장**
    ```bash
    python data_processor.py
    ```

3. **API 서버 실행**
    ```bash
    python app.py
    ```
    또는
    ```bash
    python api.py
    ```

4. **DB 데이터 확인**
    ```bash
    python check_data.py
    ```

5. **프론트엔드 확인**
    - `frontend/index.html` 파일을 브라우저에서 열기

## 주의사항

- `.env`, `data/`, `chroma_db/` 등 민감하거나 용량이 큰 파일은 git에 포함되지 않습니다.
- 대용량 DB 파일은 직접 생성하거나 별도 공유 필요

## 기여 및 문의

- Pull Request, Issue 환영합니다!
- 문의: [이메일 주소 또는 깃허브 이슈 활용] 
