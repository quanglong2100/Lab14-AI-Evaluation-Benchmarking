# Báo cáo Cá nhân - Lab Day 14: AI Evaluation Factory
**Thành viên:** Nguyễn Công Quốc Huy
**MSSV:** 2A202600389
**Vai trò:** Integration & Agent Optimization (RAG Pipeline & Metadata Tracking)

---

## 1. Các nhiệm vụ đã thực hiện (Engineering Contribution)

Tôi chịu trách nhiệm phát triển và tối ưu hóa thực thể AI Agent, đảm bảo Agent hoạt động ổn định và cung cấp đầy đủ dữ liệu cho bộ máy đánh giá.

### 1.1. Xây dựng RAG Agent thực tế
- **File thực hiện:** `agent/main_agent.py`
- Triển khai cấu trúc Agent dựa trên kiến trúc RAG (Retrieval-Augmented Generation), kết nối với cơ sở tri thức từ 3 nguồn tài liệu: Chính sách công ty, Danh mục sản phẩm và Hướng dẫn kỹ thuật.
- Sử dụng mô hình **GPT-4o** và **GPT-4o-mini** làm engine xử lý chính, thiết lập tham số `temperature=0.2` để đảm bảo tính ổn định và chính xác của câu trả lời.

### 1.2. Tối ưu hóa khâu Retrieval & Alias Resolution
- Phối hợp với Member B để triển khai hệ thống **Alias Mapping**. Agent có khả năng nhận diện các mã ID rút gọn (như `POL_001`) và tự động ánh xạ sang mã định danh đầy đủ trong hệ thống (`COMPANY_POLICY_007`).
- Đảm bảo hàm `query` luôn trả về trường `retrieved_ids`, cho phép Member C và A tính toán chỉ số Hit Rate một cách tự động.

### 1.3. Hệ thống theo dõi Token và Chi phí (Cost Estimation)
- Xây dựng module tính toán Token tiêu thụ thực tế dựa trên phản hồi của OpenAI API.
- Cài đặt hàm `_estimate_cost` dựa trên bảng giá thực tế của mô hình (Input/Output pricing), cung cấp dữ liệu đầu vào quan trọng cho báo cáo tài chính của hệ thống benchmark.

---

## 2. Giải trình Kỹ thuật (Technical Depth)

### 2.1. Kỹ thuật Grounding trong Prompt Engineering
Để đạt điểm cao ở tiêu chí **Faithfulness**, tôi đã thiết kế System Prompt cực kỳ chặt chẽ, ép Agent phải "Grounding" (chỉ trả lời dựa trên ngữ cảnh). Tôi sử dụng các câu lệnh ràng buộc như: *"Chỉ được trả lời dựa trên context được cung cấp"* và *"Nếu không có thông tin thì nói không biết"*. Điều này giúp giảm thiểu tối đa hiện tượng Hallucination (ảo giác).

### 2.2. Xử lý câu hỏi mơ hồ (Ambiguity Handling)
Tôi đã lập trình logic nhận diện ý định (Intent Recognition) cho các câu hỏi thiếu thông tin. Ví dụ, khi người dùng hỏi về "giá" mà không nêu rõ gói dịch vụ, Agent thay vì đoán mò sẽ kích hoạt hàm `_is_ambiguous` để yêu cầu người dùng làm rõ. Điều này phản ánh tư duy AI chuyên nghiệp trong môi trường doanh nghiệp.

---

## 3. Giải quyết vấn đề (Problem Solving)

- **Vấn đề (Context Overflow):** Khi Retrieval trả về quá nhiều thông tin, LLM dễ bị nhiễu và tốn nhiều token không cần thiết.
- **Giải pháp:** Tôi đã cài đặt tham số `top_k=3` và viết thêm hàm `_clean_context_excerpt` để làm sạch văn bản, loại bỏ các ký tự thừa và chỉ giữ lại những câu mang giá trị thông tin cao nhất trước khi đưa vào Prompt.
- **Vấn đề (Consistency):** Agent đôi khi trả lời bằng tiếng Anh dù context là tiếng Việt.
- **Giải pháp:** Tôi đã cập nhật System Prompt để định nghĩa rõ "Persona" của Agent là một trợ lý hỗ trợ nội bộ người Việt, yêu cầu phản hồi bằng tiếng Việt có dấu ngay cả khi các thuật ngữ kỹ thuật là tiếng Anh.

---

## 4. Kết luận
Qua bài Lab, tôi đã hiểu rõ rằng một Agent tốt không chỉ là một Agent trả lời hay, mà là một Agent có khả năng cung cấp dữ liệu "tự soi xét" (self-inspect). Việc tích hợp sâu Metadata vào Agent của tôi đã giúp toàn bộ nhóm có thể đo lường và tối ưu hóa hệ thống một cách khoa học.

---