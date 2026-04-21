# Báo cáo Cá nhân - Lab Day 14: AI Evaluation Factory

**Thành viên:** Nguyễn Anh Tài  
**MSSV:** 2A202600388  
**Vai trò:** Dataset & SDG

---

## 1. Các nhiệm vụ đã thực hiện

Trong dự án xây dựng Hệ thống đánh giá AI Agent, tôi chịu trách nhiệm chính trong việc xây dựng Dữ liệu và Chỉ số đánh giá Retrieval. Các nhiệm vụ cụ thể bao gồm:

### 1.1. Xây dựng Pipeline sinh dữ liệu tự động (SDG)

- **File thực hiện:** `data/synthetic_gen.py`
- **Kết quả:** Triển khai thành công quy trình đọc dữ liệu trực tiếp từ file **`data/chunks.jsonl`**. Điều này giúp đảm bảo bộ "đề thi" luôn đồng bộ tuyệt đối với các đoạn văn bản (chunks) thực tế mà Agent truy xuất.
- **Quy mô:** Tổng cộng đã tạo ra **60 test cases** chất lượng cao.

### 1.2. Thiết kế bộ "Red Teaming" (Adversarial Cases)

- Đưa vào **6 kịch bản tấn công/bẫy** để thử thách độ bền vững của Agent:
  - _Prompt Injection_: Kiểm tra khả năng bảo vệ thông tin mật mật khẩu.
  - _Out-of-context_: Kiểm tra khả năng nhận biết thông tin không có trong tài liệu.
  - _Ambiguous Query_: Thử thách khả năng xử lý câu hỏi thiếu thông tin rõ ràng.
  - _Goal Hijacking_, _Conflicting Info_, và _Multi-hop Reasoning_.

### 1.3. Triển khai Metrics đánh giá Retrieval

- **File thực hiện:** `engine/retrieval_eval.py`
- Hoàn thiện các thuật toán đo lường hiệu năng tìm kiếm:
  - **Hit Rate@K**: Đo lường khả năng tìm thấy tài liệu đúng trong Top-K kết quả.
  - **MRR (Mean Reciprocal Rank)**: Đánh giá thứ hạng của tài liệu đúng (vị trí càng cao điểm càng cao).
- Gắn nhãn **`expected_retrieval_ids`** khớp hoàn toàn với các mã định danh của hệ thống (ví dụ: `COMPANY_POLICY_001`, `TECHNICAL_GUIDE_002`...).

---

## 2. Giải trình Kỹ thuật (Technical Depth)

### 2.1. Tại sao cần Hit Rate và MRR?

- **Hit Rate**: Cho biết "độ phủ" của Agent. Nếu Hit Rate thấp, nghĩa là Agent đang "mù" thông tin - không tìm thấy tài liệu cần thiết để trả lời.
- **MRR**: Cho biết "độ nhạy". Một Agent tốt phải đưa được tài liệu quan trọng nhất lên vị trí số 1 (`MRR = 1`). Vị trí càng cao, LLM càng ít bị nhiễu bởi các thông tin rác xung quanh, giúp câu trả lời chính xác và tiết kiệm token hơn.

### 2.2. Tầm quan trọng của Đa dạng hóa dữ liệu

Việc đồng bộ hóa dữ liệu từ `chunks.jsonl` giúp loại bỏ hoàn toàn sai số giữa khâu "ra đề" và "tìm kiếm". Khi gán mã ID chuẩn (`COMPANY_POLICY_XXX`), chúng ta có thể đánh giá chính xác từng đoạn mã Agent tìm thấy, thay vì chỉ so sánh nội dung văn bản thuần túy.

---

## 3. Bài học kinh nghiệm & Problem Solving

- **Vấn đề**: Lúc đầu, bộ Ingestion (tạo chunk) và bộ SDG (ra đề) hoạt động độc lập, dẫn đến ID bị lệch nhau (ví dụ: bên ra đề gọi là `POL_001`, bên tìm kiếm gọi là `CHUNK_0`).
- **Giải quyết**: Tôi đã đề xuất và thực hiện việc tập trung hóa dữ liệu vào file `data/chunks.jsonl`. Sau đó, cập nhật lại `synthetic_gen.py` để đọc ID trực tiếp từ file này. Kết quả là hệ thống đánh giá hiện tại đạt độ chính xác 100% về mặt định danh, giúp việc debug khâu Retrieval trở nên cực kỳ dễ dàng.

---
