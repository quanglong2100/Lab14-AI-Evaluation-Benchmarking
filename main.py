import asyncio
import json
import os
import time
from typing import List, Dict
from dotenv import load_dotenv

# Nạp biến môi trường từ file .env
load_dotenv()

# Import các module thực tế từ các thành viên khác
from agent.main_agent import MainAgent
from engine.retrieval_eval import RetrievalEvaluator
from engine.llm_judge import LLMJudge
from engine.runner import BenchmarkRunner

# Wrapper để kết nối RetrievalEvaluator thật vào BenchmarkRunner
class RealEvaluator:
    def __init__(self):
        self.retrieval_engine = RetrievalEvaluator(top_k=3)

    async def score(self, test_case: Dict, agent_response: Dict):
        """Tính toán Hit Rate và MRR dựa trên dữ liệu thật từ Agent"""
        expected_ids = test_case.get("expected_retrieval_ids", [])
        retrieved_ids = agent_response.get("retrieved_ids", [])
        
        hit_rate = self.retrieval_engine.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.retrieval_engine.calculate_mrr(expected_ids, retrieved_ids)
        
        return {
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": mrr
            }
        }

async def run_evaluation_pipeline(version_name: str, model_name: str):
    """Pipeline chạy benchmark chi tiết cho một phiên bản Agent"""
    print(f"\n🚀 Đang khởi động Benchmark: {version_name} ({model_name})")
    
    # 1. Khởi tạo các thành phần thực tế
    agent = MainAgent()
    agent.model_name = model_name # Gán model để giả lập V1 vs V2
    
    evaluator = RealEvaluator()
    judge = LLMJudge()
    runner = BenchmarkRunner(agent, evaluator, judge)

    # 2. Load Golden Dataset
    data_path = "data/golden_set.jsonl"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Thiếu file {data_path}. Hãy chạy SDG trước!")

    with open(data_path, "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    # 3. Chạy Benchmark (Async) với batch_size=1 để tránh lỗi kết nối
    results = await runner.run_all(dataset, batch_size=1)

    # 4. Tính toán Metrics tổng hợp
    total = len(results)
    if total == 0:
        print("⚠️ Warning: No valid results to aggregate.")
        return [], {}

    avg_score = sum(r.get("judge", {}).get("final_score", 0) for r in results) / total
    avg_hit_rate = sum(r.get("retrieval", {}).get("retrieval", {}).get("hit_rate", 0) for r in results) / total
    avg_agreement = sum(r.get("judge", {}).get("agreement_rate", 0) for r in results) / total
    
    # 5. Tính toán chi phí (Cost per Eval)
    # Lấy cost từ Agent (RAG) + ước tính cost từ Judge (thường Judge tốn gấp đôi Agent)
    total_agent_cost = sum(r.get("agent_cost", 0) for r in results) 
    # Giả lập cost của Judge dựa trên model (khoảng 0.005$ mỗi case cho Multi-judge)
    estimated_judge_cost = total * 0.005 
    
    total_cost = total_agent_cost + estimated_judge_cost
    cost_per_eval = total_cost / total

    summary = {
        "metadata": {
            "version": version_name,
            "model": model_name,
            "total": total,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "metrics": {
            "avg_score": round(avg_score, 2),
            "hit_rate": round(avg_hit_rate, 2),
            "agreement_rate": round(avg_agreement, 2),
            "cost_per_eval": round(cost_per_eval, 5),
            "total_cost_usd": round(total_cost, 4)
        }
    }
    
    return results, summary

async def main():
    print("=== AI EVALUATION FACTORY: REGRESSION MODE ===")
    
    # BƯỚC 1: Chạy Benchmark cho V1 (Base - dùng model rẻ gpt-4o-mini)
    v1_results, v1_summary = await run_evaluation_pipeline("Agent_V1_Base", "gpt-4o-mini")
    
    # BƯỚC 2: Chạy Benchmark cho V2 (Optimized - dùng gpt-4o hoặc prompt mới)
    # Ở đây ta giả lập V2 bằng cách chạy lại (trong thực tế bạn có thể thay đổi Agent logic)
    v2_results, v2_summary = await run_evaluation_pipeline("Agent_V2_Optimized", "gpt-4o")
    
    # BƯỚC 3: So sánh kết quả (Regression Analysis)
    score_v1 = v1_summary["metrics"]["avg_score"]
    score_v2 = v2_summary["metrics"]["avg_score"]
    hit_v1 = v1_summary["metrics"]["hit_rate"]
    hit_v2 = v2_summary["metrics"]["hit_rate"]
    
    delta_score = score_v2 - score_v1
    delta_hit = hit_v2 - hit_v1

    print("\n" + "="*50)
    print("📊 KẾT QUẢ SO SÁNH (V1 vs V2)")
    print("-" * 50)
    print(f"V1: Score {score_v1:.2f} | Hit Rate {hit_v1*100}%")
    print(f"V2: Score {score_v2:.2f} | Hit Rate {hit_v2*100}%")
    print(f"Delta: Score ({delta_score:+.2f}) | Hit Rate ({delta_hit:+.2f})")
    print(f"Cost per Eval (V2): ${v2_summary['metrics']['cost_per_eval']}")
    print("="*50)

    # BƯỚC 4: Logic Release Gate (Auto-Gate)
    # Điều kiện: Score không giảm VÀ Hit Rate không giảm
    is_approved = delta_score >= 0 and delta_hit >= 0
    
    if is_approved:
        decision = "✅ APPROVE: Bản cập nhật vượt qua bài kiểm tra chất lượng."
    else:
        decision = "❌ REJECT: Bản cập nhật bị lỗi hồi quy (Regression detected)."
    
    print(f"\n🚀 QUYẾT ĐỊNH CUỐI CÙNG: {decision}\n")

    # BƯỚC 5: Xuất báo cáo đúng chuẩn check_lab.py
    os.makedirs("reports", exist_ok=True)
    
    # Luôn lưu kết quả mới nhất (V2) vào file summary để chấm điểm
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
        
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        # Ghi kết quả chi tiết kèm theo quyết định release
        output_data = {
            "decision": decision,
            "regression_details": {"delta_score": delta_score, "delta_hit": delta_hit},
            "cases": v2_results
        }
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("✅ Đã ghi báo cáo vào thư mục /reports. Sẵn sàng chạy check_lab.py!")

if __name__ == "__main__":
    asyncio.run(main())
