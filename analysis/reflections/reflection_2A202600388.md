# Báo cáo Cá nhân - Lab Day 14: AI Evaluation Factory
**Thành viên:** Nguyễn Anh Tài  
**MSSV:** 2A202600388  
**Vai trò:** Dataset & SDG

---

## 1. Các nhiệm vụ đã thực hiện

Trong dự án xây dựng Hệ thống đánh giá AI Agent, tôi chịu trách nhiệm chính trong việc xây dựng "Đề thi" (Dữ liệu) và "Thước đo" (Chỉ số đánh giá Retrieval). Các nhiệm vụ cụ thể bao gồm:

### 1.1. Xây dựng Pipeline sinh dữ liệu tự động (SDG)
- **File thực hiện:** `data/synthetic_gen.py`
- **Kết quả:** Triển khai thành công quy trình đọc tài liệu từ thư mục `docs/`, thực hiện chunking theo ngữ cảnh và sử dụng LLM để sinh dữ liệu.
- **Quy mô:** Tổng cộng đã tạo ra **70 test cases**.

### 1.2. Thiết kế bộ "Red Teaming" (Adversarial Cases)
- Đưa vào **6 kịch bản tấn công/bẫy** để thử thách độ bền vững của Agent:
    - *Prompt Injection*: Thử thách khả năng bảo mật mật khẩu.
    - *Out-of-context*: Kiểm tra khả năng từ chối trả lời khi không có dữ liệu (tránh Hallucination).
    - *Ambiguous*: Kiểm tra khả năng hỏi lại (Clarify) khi câu hỏi thiếu thông tin.
    - *Goal Hijacking*, *Conflicting Info*, và *Multi-hop Reasoning*.

### 1.3. Triển khai Metrics đánh giá Retrieval
- **File thực hiện:** `engine/retrieval_eval.py`
- Hoàn thiện các thuật toán đo lường hiệu năng tìm kiếm:
    - **Hit Rate@K**: Đo lường xem tài liệu đúng có nằm trong danh sách tìm kiếm hay không.
    - **MRR (Mean Reciprocal Rank)**: Đánh giá vị trí trung bình của tài liệu đúng trong kết quả trả về.
- Gắn nhãn **`expected_retrieval_ids`** cho toàn bộ 70 cases để làm căn cứ chấm điểm tự động.

---

## 2. Giải trình Kỹ thuật (Technical Depth)

### 2.1. Tại sao cần Hit Rate và MRR?
- **Hit Rate**: Cho biết "độ phủ" của Agent. Nếu Hit Rate thấp, nghĩa là Agent đang "mù" thông tin - không tìm thấy tài liệu cần thiết để trả lời.
- **MRR**: Cho biết "độ nhạy". Một Agent tốt phải đưa được tài liệu quan trọng nhất lên vị trí số 1 (`MRR = 1`). Vị trí càng cao, LLM càng ít bị nhiễu bởi các thông tin rác xung quanh, giúp câu trả lời chính xác và tiết kiệm token hơn.

### 2.2. Tầm quan trọng của Red Teaming trong SDG
Việc sinh dữ liệu dễ (Easy) chỉ giúp biết Agent có hoạt động hay không. Việc đưa vào các câu hỏi bẫy (Red Teaming) giúp chúng ta đánh giá được **giới hạn an toàn (Safety)** và **độ thông minh thực sự** của Agent. Một AgentExpert phải biết nói "Tôi không biết" thay vì bịa chuyện khi gặp câu hỏi nằm ngoài context.

---

## 3. Bài học kinh nghiệm & Problem Solving
- **Vấn đề**: Khi sinh dữ liệu tự động, đôi khi LLM tạo ra các câu hỏi quá đơn giản hoặc bị trùng lặp.
- **Giải quyết**: Tôi đã điều chỉnh Prompt trong `synthetic_gen.py` để yêu cầu đa dạng hóa loại câu hỏi (Tại sao, Như thế nào, So sánh...) và chia tài liệu thành các chunks nhỏ dựa trên cấu trúc đề mục (##) để giữ ngữ cảnh tốt nhất.

---