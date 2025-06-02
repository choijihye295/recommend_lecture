class QuestionClassifier:
    def classify(self, question: str) -> str:
        question = question.lower()
        if "교수님" in question or "강의 정보" in question:
            return "정보형"
        elif any(word in question for word in ["추천", "어떤", "뭐가"]):
            if "학년" in question or "실습" in question or "과제" in question:
                return "조건형"
            return "추천형"
        return "기타"

#설명
'''
질문의 유형을 나누는 코드임. = 분류기!!!
정보형 : 교수명, 강의명 등 정보성 질문
조건형 : 학년, 분반, 등 조건 필터 + 추천
추천형 : ai, 실습 중심 등 추천

현재 사용 안함
'''