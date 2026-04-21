import asyncio
from typing import Dict, Any
import logging
import json
import google.generativeai as genai

logger = logging.getLogger(__name__)

class LLMJudge:
    def __init__(self, primary_model: str='gemini-1.5-pro', secondary_model: str='gemini-1.5-flash'):
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

        # Cấu hình model để trả về JSON 100% hợp lệ, tránh lỗi parse
        self.generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
        )

        self.models = {
            self.primary_model: genai.GenerativeModel(self.primary_model, generation_config=self.generation_config),
            self.secondary_model: genai.GenerativeModel(self.secondary_model, generation_config=self.generation_config),
        }
    
    async def _call_llm(self, model: str, system_prompt: str, user_prompt: str) -> Dict:
        """
        Gọi Gemini + parse JSON output một cách an toàn
        """
        def sync_call():
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.models[model].generate_content(full_prompt)
            return response.text

        # chạy sync SDK trong thread để không block event loop
        raw_text = await asyncio.to_thread(sync_call)

        try:
            # Vì đã config response_mime_type="application/json" nên raw_text chắc chắn là JSON
            return json.loads(raw_text)
        except Exception as e:
            logger.warning(f"Failed to parse JSON from {model}: {e}. Raw text: {raw_text}")
            # fallback cực đơn giản cho lab
            return {
                "accuracy": 3,
                "faithfulness": 3,
                "professionalism": 3,
                "reasoning": "Fallback due to parse error"
            }
        
    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        EXPERT TASK: Gọi ít nhất 2 model.
        Tính toán sự sai lệch. Nếu lệch >= 2 điểm, cần logic xử lý.
        """
        user_content = f"Question:{question}\nAnswer:{answer}\nGround Truth:{ground_truth}"

        task1 = self._call_llm(self.primary_model, self.rubric_prompt, user_content)
        task2 = self._call_llm(self.secondary_model, self.rubric_prompt, user_content)

        res1, res2 = await asyncio.gather(task1, task2)
        
        # Dùng .get() với default=3 để tránh lỗi KeyError nếu JSON bị mất trường
        score_1 = res1.get("accuracy", 3)
        score_2 = res2.get("accuracy", 3)

        delta = abs(score_1 - score_2)
        agreement_rate = 1.0 - (delta / 4.0)

        if delta >= 2:
            # Chọn điểm thấp hơn khi có xung đột lớn (đánh giá khắt khe hơn)
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
                "avg_accuracy": (score_1 + score_2) / 2,
                "avg_faithfulness": (res1.get("faithfulness", 3) + res2.get("faithfulness", 3)) / 2
            },
        }

    async def check_position_bias(self, question: str, response_a: str, response_b: str):
        """
        Kiểm tra position bias bằng cách hỏi trực tiếp A vs B
        """
        # Tạo model text thường (không ép JSON) cho tác vụ này vì đầu ra chỉ cần 1 chữ cái
        text_model = genai.GenerativeModel(self.primary_model)

        prompt_1 = f"Question: {question}\nResponse A: {response_a}\nResponse B: {response_b}\n\nChỉ trả lời 1 ký tự: 'A' hoặc 'B' (response nào tốt hơn)"
        prompt_2 = f"Question: {question}\nResponse A: {response_b}\nResponse B: {response_a}\n\nChỉ trả lời 1 ký tự: 'A' hoặc 'B' (response nào tốt hơn)"

        def sync_call(prompt):
            return text_model.generate_content(prompt).text.strip().upper()

        res1 = await asyncio.to_thread(sync_call, prompt_1)
        res2 = await asyncio.to_thread(sync_call, prompt_2)

        # Lấy chữ cái A hoặc B từ kết quả
        choice_1 = "A" if "A" in res1 else "B"
        choice_2 = "A" if "A" in res2 else "B"

        # Đổi chỗ 2 response ở prompt 2. 
        # Nếu model lúc nào cũng chọn chữ "A" (dù response đã bị đổi vị trí), nghĩa là model bị Position Bias.
        if choice_1 == choice_2: 
            return {
                "bias": True,
                "detail": f"Model consistently chose Position {choice_1} regardless of content."
            }

        return {
            "bias": False,
            "detail": "Model correctly tracked the best response."
        }
