# Báo cáo Cá nhân - Lab Day 14: AI Evaluation Factory
**Thành viên:** Hoàng Bá Minh Quang
**MSSV:** 2A202600063
**Vai trò:** AI Backend & Engine Developer (Multi-Judge & Async Runner)

---

## 1. Các nhiệm vụ đã thực hiện (Engineering Contribution)

Tôi chịu trách nhiệm xây dựng hạ tầng kỹ thuật cốt lõi để thực thi việc benchmark và bộ máy giám khảo AI tự động.

### 1.1. Hoàn thiện Async Runner tối ưu hiệu suất
- **File thực hiện:** `engine/runner.py`
- Triển khai cơ chế chạy song song (Parallel Processing) sử dụng `asyncio.gather`. 
- Cấu hình `batch_size` linh hoạt để tối ưu tốc độ thực thi (hoàn thành 50 cases trong chưa đầy 2 phút) nhưng vẫn đảm bảo không bị vượt định mức Rate Limit của OpenAI API.
- Tích hợp việc thu thập Metadata từ Agent (Token usage, Latency) để phục vụ khâu tính toán chi phí của Member C.

### 1.2. Triển khai Hệ thống Multi-Judge Consensus
- **File thực hiện:** `engine/llm_judge.py`
- Xây dựng lớp `LLMJudge` có khả năng gọi đồng thời hai mô hình: **GPT-4o** (Giám khảo chính) và **GPT-4o-mini** (Giám khảo đối soát).
- Thiết lập bộ **Rubric chấm điểm** chi tiết dựa trên 3 tiêu chí: Accuracy, Faithfulness và Professionalism.

### 1.3. Logic xử lý đồng thuận và xung đột (Consensus Logic)
- Viết thuật toán tính toán **Agreement Rate** để đo lường độ tin cậy của kết quả chấm điểm.
- Triển khai cơ chế xử lý xung đột: Nếu hai giám khảo lệch nhau quá 2 điểm (Conflict), hệ thống sẽ tự động lấy điểm số thấp nhất (`min_score`) để đảm bảo tính khắt khe và an toàn cho hệ thống AI.

---

## 2. Giải trình Kỹ thuật (Technical Depth)

### 2.1. Tại sao cần Multi-Judge thay vì Single-Judge?
Trong môi trường thực tế, một mô hình LLM duy nhất có thể mắc lỗi "Position Bias" (thiên vị vị trí) hoặc "Self-preference" (ưu tiên câu trả lời giống phong cách của nó). Việc tôi triển khai Multi-Judge giúp triệt tiêu các sai số này, đảm bảo kết quả benchmark công tâm và phản ánh đúng năng lực của Agent.

### 2.2. Cơ chế tính toán Agreement Rate
Tôi sử dụng công thức: $Agreement = 1 - \frac{|Score_1 - Score_2|}{4}$. 
Chỉ số này (đạt 94% trong lần chạy cuối) chứng minh rằng bộ Rubric tôi thiết kế rất minh bạch, giúp các model LLM khác nhau có cái nhìn thống nhất về chất lượng câu trả lời.

---

## 3. Giải quyết vấn đề (Problem Solving)

- **Vấn đề:** Khi chạy benchmark với số lượng case lớn, API OpenAI thường trả về lỗi `429 Too Many Requests`.
- **Giải pháp:** Tôi đã thiết kế lại hàm `run_all` trong `runner.py`, chia nhỏ dataset thành từng đợt (batches) và sử dụng `asyncio.sleep` giữa các đợt để "giãn" lưu lượng truy cập. Đồng thời, tôi thêm cơ chế `max_retries` để tự động thử lại khi gặp lỗi mạng tạm thời, giúp hệ thống không bị crash giữa chừng.
- **Vấn đề:** Ban đầu, Judge trả về văn bản tự do khiến code không thể parse điểm để tính toán.
- **Giải pháp:** Tôi đã tận dụng tính năng **JSON Mode** của OpenAI API (`response_format={"type": "json_object"}`) và thiết kế lại System Prompt để ép model luôn trả về đúng cấu trúc JSON mong muốn.

---

## 4. Kết luận
Tôi đã hoàn thành một Engine đánh giá có khả năng mở rộng cao (Scalable). Hệ thống không chỉ dừng lại ở việc chấm điểm mà còn cung cấp đầy đủ dữ liệu kỹ thuật để nhóm có thể thực hiện phân tích thất bại một cách sâu sắc nhất.

---