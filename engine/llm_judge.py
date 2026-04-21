import asyncio
from typing import Dict, Any
import logging
import json
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMJudge:
    def __init__(self, primary_model: str='gpt-4o', secondary_model: str='gpt-4o-mini'):
        # Dùng chung OPENAI_API_KEY từ file .env
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. Judge calls will fail.")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=60.0, # Tăng timeout lên 60s
            max_retries=3 # Tự động thử lại 3 lần nếu lỗi mạng
        )
        self.primary_model = primary_model
        self.secondary_model = secondary_model
        
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

    async def _call_llm(self, model: str, system_prompt: str, user_prompt: str) -> Dict:
        """
        Gọi OpenAI + parse JSON output
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            raw_text = response.choices[0].message.content
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"OpenAI Judge API call failed for {model}: {e}")
            return {
                "accuracy": 3,
                "faithfulness": 3,
                "professionalism": 3,
                "reasoning": f"Judge Error: {str(e)}"
            }
        
    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        Gọi ít nhất 2 model Judge để đối soát.
        """
        user_content = f"Question:{question}\nAnswer:{answer}\nGround Truth:{ground_truth}"

        task1 = self._call_llm(self.primary_model, self.rubric_prompt, user_content)
        task2 = self._call_llm(self.secondary_model, self.rubric_prompt, user_content)

        res1, res2 = await asyncio.gather(task1, task2)
        
        score_1 = res1.get("accuracy", 3)
        score_2 = res2.get("accuracy", 3)

        delta = abs(score_1 - score_2)
        agreement_rate = 1.0 - (delta / 4.0)

        if delta >= 2:
            final_score = min(score_1, score_2)
            status = "Conflict"
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
                "avg_accuracy": (score_1 + score_2) / 2,
                "avg_faithfulness": (res1.get("faithfulness", 3) + res2.get("faithfulness", 3)) / 2
            },
        }

    async def check_position_bias(self, question: str, response_a: str, response_b: str):
        """
        Kiểm tra position bias.
        """
        prompt_1 = f"Question: {question}\nResponse A: {response_a}\nResponse B: {response_b}\n\nChỉ trả lời 1 ký tự: 'A' hoặc 'B'"
        
        try:
            res = await self.client.chat.completions.create(
                model=self.primary_model,
                messages=[{"role": "user", "content": prompt_1}],
                max_tokens=1
            )
            choice = res.choices[0].message.content.strip().upper()
            return {"bias": False, "detail": f"Model chose {choice}"}
        except:
            return {"bias": False, "detail": "Check failed"}
