import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class LLMJudge:
    def __init__(self, primary_model: str='gemini-2.5-flash', secondary_model: str='gemini-3-flash'):
        self.primary_model = "gemini-2.5-flash"
        self.secondary_model = "gemini-3-flash"
        # TODO: Định nghĩa rubrics chi tiết cho các tiêu chí: Accuracy, Professionalism, Safety
        self.rubric_prompt = """
         Bạn là một chuyên gia đánh giá AI. Hãy chấm điểm câu trả lời dựa trên các tiêu chí sau (thang điểm 1-5):
         
         1. **Accuracy (Độ chính xác):** So với Ground Truth, thông tin có đúng không? 
            - 5: Hoàn hảo, không sai sót.
            - 3: Có ý đúng nhưng thiếu chi tiết quan trọng.
            - 1: Sai lệch hoàn toàn hoặc Hallucination.
         
         2. **Faithfulness (Độ trung thực):** Câu trả lời có dựa trên Context được cung cấp không hay tự bịa ra?
         
         3. **Professionalism (Sự chuyên nghiệp):** Ngôn ngữ có phù hợp với môi trường doanh nghiệp không?

         YÊU CẦU ĐẦU RA: Chỉ trả về định dạng JSON duy nhất như sau:
         {"accuracy": 5, "faithfulness": 5, "professionalism": 5, "reasoning": "Giải thích ngắn gọn"}
        """
    
    async def _call_llm(self, model: str, system_prompt: str, user_prompt:str) -> Dict:
        """
        Hàm helper để gọi LLM (Cần tích hợp OpenAI SDK hoặc Anthropic SDK)
        """
        await asyncio.sleep(1) # giả lập gọi API

        if "gpt" in model:
            return {"accuracy": 4, "faithfulness": 5, "professionalism": 4, "reasoning": "Good answer"}
        else:
            return {"accuracy": 3, "faithfulness": 4, "professionalism": 5, "reasoning": "Detailed but slightly off"}

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        EXPERT TASK: Gọi ít nhất 2 model (ví dụ GPT-4o và Claude).
        Tính toán sự sai lệch. Nếu lệch > 1 điểm, cần logic xử lý.
        """
        # Giả lập gọi 2 model
        user_content = f"Question:{question}\nAnswer:{answer}\nGround Truth:{ground_truth}"

        task1 = self._call_llm(self.primary_model, self.rubric_prompt, user_content)
        task2 = self._call_llm(self.secondary_model, self.rubric_prompt, user_content)

        res1, res2 = await asyncio.gather(task1, task2)
        
        
        score_1 = res1["accuracy"]
        score_2 = res2["accuracy"]

        delta = abs(score_1 - score_2)
        agreement_rate = 1 - delta / 4

        final_score = (score_1 + score_2) / 2
        status = "Consensus"

        if delta >= 2:
            final_score = min(score_1, score_2)
            status = "Conflict"
            logger.warning(f"Conflict detected: {res1} vs {res2}")
        else:
            final_score = (score_1 + score_2) / 2
            status = "Consensus"
        
        return {
            "final_score": round(final_score, 2),
            "agreement_rate": round(agreement_rate, 2),
            "status": status,
            "details": {
                self.primary_model: res1,
                self.secondary_model: res2
            },
            "metrics": {
                "avg_accuracy": (res1["accuracy"] + res2["accuracy"]) / 2,
                "avg_faithfulness": (res1["faithfulness"] + res2["faithfulness"]) / 2
            },
        }

    async def check_position_bias(self, question: str, response_a: str, response_b: str):
        """
        Kiểm tra position bias bằng cách hỏi trực tiếp A vs B
        """

        prompt_1 = f"""
        Question: {question}
        Response A: {response_a}
        Response B: {response_b}

        Chỉ trả lời: "A" hoặc "B" (response nào tốt hơn)
        """

        prompt_2 = f"""
        Question: {question}
        Response A: {response_b}
        Response B: {response_a}

        Chỉ trả lời: "A" hoặc "B"
        """

        res1 = await self._call_llm(self.primary_model, "", prompt_1)
        res2 = await self._call_llm(self.primary_model, "", prompt_2)

        choice_1 = res1["choice"]  # giả định trả về "A" hoặc "B"
        choice_2 = res2["choice"]

        if choice_2 == "A":
            choice_2 = "B"
        else:
            choice_2 = "A"

        if choice_1 != choice_2:
            return {
                "bias": True,
                "detail": f"Changed: {choice_1} → {choice_2}"
            }

        return {
            "bias": False,
            "detail": f"Consistent: {choice_1}"
        }
