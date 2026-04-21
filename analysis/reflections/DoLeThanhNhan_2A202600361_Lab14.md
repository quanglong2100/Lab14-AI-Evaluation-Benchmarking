# Báo cáo Cá nhân - Lab Day 14: AI Evaluation Factory
**Thành viên:** Đỗ Lê Thành Nhân 
**MSSV:** 2A202600361  
**Vai trò:** AI Data Analyst (Failure Analysis & Optimization Strategy)

---

## 1. Các nhiệm vụ đã thực hiện (Engineering Contribution)

Trong dự án này, tôi chịu trách nhiệm chính về việc phân tích "hậu kiểm" sau khi hệ thống Benchmark hoàn tất quá trình chạy dữ liệu.

### 1.1. Thực hiện Phân cụm lỗi (Failure Clustering)
- **File thực hiện:** `analysis/failure_analysis.md`
- Sau khi nhận file `benchmark_results.json` từ Member C, tôi đã tiến hành rà soát 50 test cases để phân loại các hành vi lỗi của Agent.
- Tôi đã xác định được 3 nhóm lỗi chính: **Retrieval Miss** (Lỗi tìm kiếm), **Information Gap** (Lỗi thiếu thông tin) và **Hallucination** (Lỗi ảo giác).

### 1.2. Phân tích nguyên nhân gốc rễ bằng kỹ thuật "5 Whys"
- Tôi đã chọn ra các case có điểm thấp nhất (1.0 - 2.0 điểm) để thực hiện quy trình "5 Whys". 
- Đặc biệt tập trung vào các trường hợp Agent trả lời "Không biết" (ví dụ: case về Gói Basic) để tìm ra điểm nghẽn nằm ở khâu Chunker (cắt dữ liệu) hay khâu Retriever (truy xuất).

### 1.3. Đề xuất kế hoạch cải tiến (Action Plan)
- Dựa trên các con số thực tế, tôi đã đề xuất lộ trình tối ưu hóa Agent cho nhóm: chuyển đổi từ Lexical Search sang Hybrid Search và điều chỉnh lại độ dài Chunk để giữ trọn ngữ cảnh.

---

## 2. Giải trình Kỹ thuật (Technical Depth)

### 2.1. Hiểu về mối liên hệ giữa Retrieval Quality và Answer Quality
Qua phân tích, tôi nhận thấy một quy luật: Điểm số của Judge tỷ lệ thuận với tính chính xác của Retrieval. Tuy nhiên, ở phiên bản V2 (GPT-4o), ngay cả khi **Hit Rate chỉ đạt 34%**, điểm trung bình vẫn tăng lên **3.95**. Điều này chứng tỏ một model mạnh có khả năng "cứu vãn" các thông tin mờ nhạt từ Context, nhưng để đạt điểm tuyệt đối (5.0), việc cải thiện tầng Retrieval là bắt buộc.

### 2.2. Phân tích sự khác biệt giữa Lexical Search và Semantic Search
Tôi đã giải trình trong báo cáo nhóm rằng con số 34% Hit Rate là hệ quả của việc sử dụng **Lexical Search (Token Overlap)**. Kỹ thuật này quá máy móc khi chỉ bắt các từ trùng khớp hoàn toàn, dẫn đến việc Agent bị "mù" trước các câu hỏi sử dụng từ đồng nghĩa hoặc cách diễn đạt khác. Đây là kiến thức cốt lõi để nhóm định hướng nâng cấp lên Vector Embedding trong tương lai.

---

## 3. Giải quyết vấn đề (Problem Solving)

- **Vấn đề (Conflict Management):** Có những trường hợp hai mô hình Judge cãi nhau (Agreement Rate thấp ở một số case cụ thể).
- **Giải pháp:** Tôi đã trực tiếp đọc nội dung `reasoning` của từng Judge. Tôi phát hiện ra GPT-4o-mini thường quá khắt khe với các câu trả lời ngắn, trong khi GPT-4o đánh giá cao tính trung thực (nói không biết khi context thiếu). Từ đó, tôi đã hỗ trợ Member A điều chỉnh lại System Prompt của Judge để thống nhất rằng: "Trung thực là ưu tiên số 1, ngắn gọn là ưu tiên số 2".
- **Vấn đề (Data Noise):** Khi Retrieval trả về các đoạn văn bản (chunks) bị cắt vụn, Agent thường đưa ra câu trả lời thiếu đầu đuôi.
- **Giải pháp:** Tôi đã đề xuất với Member B (Data) sử dụng kỹ thuật **Context Enrichment** (thêm tiêu đề section vào mỗi chunk) để Agent luôn biết đoạn văn bản đó thuộc về tài liệu nào, giúp câu trả lời chuyên nghiệp hơn.

---

## 4. Kết luận
Vai trò Analyst của tôi giúp nhóm không chỉ dừng lại ở việc "nhìn thấy con số" mà còn "hiểu được con số". Những phân tích của tôi là cơ sở khoa học để nhóm đưa ra quyết định **Approve Release** cho phiên bản V2 và có lộ trình rõ ràng cho phiên bản V3.

---