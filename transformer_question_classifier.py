from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

class TransformerQuestionClassifier:
    def __init__(self):
        MODEL_NAME = "klue/roberta-base" #직접 튜닝못해서 가져다가 씀.
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)
        self.label_map = {
            0: "추천형",
            1: "조건형",
            2: "정보형"
        }

    def classify(self, question: str) -> str:
        # 1. Transformer 기반 예측
        inputs = self.tokenizer(question, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)
        pred_index = torch.argmax(probs, dim=1).item()
        pred_label = self.label_map.get(pred_index, "기타")

        # 2. Softmax 확률이 낮을 경우 rule fallback
        confidence = probs[0][pred_index].item()
        if confidence < 0.6:  # 60% 미만이면 rule 기반으로 보완
            pred_label = self.rule_based_classify(question)

        return pred_label

    def rule_based_classify(self, question: str) -> str:
        q = question.lower()
        if "교수" in q or "강의명" in q or "이메일" in q or "연락처" in q:
            return "정보형"
        elif any(keyword in q for keyword in ["학년", "과제", "실습", "조건", "전공", "수강신청"]):
            return "조건형"
        elif any(keyword in q for keyword in ["추천", "어떤", "뭐가", "알려줘", "괜찮은", "좋은"]):
            return "추천형"
        return "기타"
