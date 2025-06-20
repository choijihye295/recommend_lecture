from vector_store import get_vector_store
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from question_classifier import QuestionClassifier
from transformer_question_classifier import TransformerQuestionClassifier
from prompts import RECOMMEND_PROMPT, INFO_PROMPT, CONDITION_PROMPT
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class MultiChainRecommender:
    def __init__(self):
        self.vectorstore = get_vector_store()
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_key=OPENAI_API_KEY,
            #max_tokens=512 #응답 길이 최대 토큰 제한
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"  # 꼭 넣어야함. 여기 저장해야됨!
        )

        #질문 분류기 > 클래스 선택 가능
        #self.classifier = QuestionClassifier() # 질문 분류하는 클래스 (미리 만들어둠. question_classifier.py)

        self.classifier = TransformerQuestionClassifier() #트렌스포머로 보완한 클래스

    def get_chain(self, question):
        q_type = self.classifier.classify(question)
        prompt = {
            "추천형": RECOMMEND_PROMPT,
            "조건형": CONDITION_PROMPT,
            "정보형": INFO_PROMPT
        }.get(q_type, RECOMMEND_PROMPT)
        # 질문 유형별로 프롬프트 선택 (미리 만들어둠. prompts.py)

        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5}) #강의 개수 검색 줄임
        #벡터db에서 유사한 강의 계획서 검색 (일단 10개정도)

        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            output_key="answer",
            combine_docs_chain_kwargs={"prompt": prompt},
            return_source_documents=True
        )

    def recommend(self, question: str): #최종실행
        chain = self.get_chain(question)
        return chain.invoke({"question": question})
    #위에서 구성한 체인을 실행하여 응답 얻음
