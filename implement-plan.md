  📑 Kế hoạch phân công chi tiết (Team 5 Người)

  | Thành viên | Vai trò        | Task chính & File cần sửa | Ghi chú (Dependency) |
|------------|---------------|---------------------------|----------------------|
| A (Trưởng nhóm) | AI/Backend | **Engine & Async Runner**<br>1. Hoàn thiện `engine/runner.py`: tối ưu async, tính cost/token.<br>2. Cài đặt Multi-Judge trong `engine/llm_judge.py` (GPT-4o + Claude 3.5).<br>3. Xử lý logic consensus & agreement rate. | Cần API key của 2 model |
| B | Data Engineer | **SDG & Retrieval Metrics**<br>1. Code `data/synthetic_gen.py`: sinh 50+ Q&A.<br>2. Thêm `expected_retrieval_ids` vào Golden Set.<br>3. Hoàn thiện `engine/retrieval_eval.py`: `hit_rate`, `MRR`. | Làm trước để có data cho team |
| C | DevOps/QA | **Regression & Reports**<br>1. Sửa `main.py`: so sánh V1/V2.<br>2. Code Release Gate (auto approve/reject).<br>3. Format `reports/summary.json` đúng chuẩn `check_lab.py`. | Chờ A và B |
| D | Analyst | **Failure Analysis**<br>1. Chạy benchmark, ghi vào `analysis/failure_analysis.md`.<br>2. Phân cụm lỗi (auto hoặc 5 Whys).<br>3. Đề xuất cải tiến agent (chunking, prompt...). | Chờ kết quả từ C |
| E | Integration | **Agent Optimization & Pipeline**<br>1. Sửa `agent/main_agent.py`: dùng agent thật.<br>2. Đảm bảo output có `retrieved_ids`.<br>3. Hỗ trợ A tích hợp judge vào pipeline. | Cần agent từ các lab trước |

  💡 Lưu ý để đạt điểm tuyệt đối (Expert Tips):
   * Thành viên A: Nhớ implement "Position Bias check" (đảo thứ tự câu trả lời khi đưa cho Judge) để chứng minh tính khách quan.
   * Thành viên B: Golden Set cần có ít nhất 5 câu hỏi "Red Teaming" (câu hỏi bẫy) để thử thách Agent.
   * Thành viên C: Đảm bảo summary.json có thông số cost_per_eval (tính dựa trên token usage).