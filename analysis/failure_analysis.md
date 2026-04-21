

# 📊 Group Report: AI Evaluation Factory Analysis (Final Results)
**Dự án:** Hệ thống Benchmarking và Đánh giá Hồi quy cho Support Agent  
**Phiên bản đánh giá:** V1 (gpt-4o-mini) vs V2 (gpt-4o)

---

## 1. Tổng quan Benchmark (Executive Summary)
Sau khi chạy Pipeline đánh giá hồi quy trên bộ Golden Dataset (50 cases), nhóm đã thu được các chỉ số quan trọng sau:

*   **Kết quả tổng thể (V2):**
    *   **Điểm trung bình (LLM-Judge):** 3.95 / 5.0 🟢 (Tăng so với 3.63 của V1).
    *   **Tỉ lệ tìm kiếm đúng (Hit Rate):** 34.0% ⚠️ (Không đổi giữa 2 phiên bản).
    *   **Độ đồng thuận (Agreement Rate):** 94.0% ✅ (Chứng minh bộ máy Multi-Judge hoạt động cực kỳ ổn định).
*   **Hiệu năng & Chi phí:**
    *   **Cost per Eval (V2):** $0.00632 / case.
    *   **Tổng chi phí:** $0.316 cho toàn bộ 50 cases.
*   **Quyết định:** **✅ APPROVE**. Bản cập nhật V2 (gpt-4o) giúp tăng chất lượng câu trả lời (+0.32 điểm) dù chi phí cao hơn, đạt tiêu chuẩn release.

---

## 2. Phân nhóm lỗi (Failure Clustering)
Dựa trên kết quả chạy thực tế, nhóm nhận thấy các lỗi tập trung vào 3 nhóm chính:

| Nhóm lỗi                  | Số lượng | Nguyên nhân dự kiến                                                                                |
| :------------------------ | :------: | :------------------------------------------------------------------------------------------------- |
| **Retrieval Failure**     |    33    | Hệ thống tìm kiếm (lexical search) chỉ dựa trên token overlap nên bỏ lỡ nhiều tài liệu quan trọng. |
| **Information Gap**       |    5     | Agent trả lời "Không biết" dù thông tin có trong Ground Truth (ví dụ: Case Ingestion Engine).      |
| **Detail Incompleteness** |    4     | Agent trả lời đúng ý chính nhưng thiếu chi tiết kỹ thuật nhỏ (ví dụ: Case Chunk size).             |

---

## 3. Phân tích 5 Whys (Root Cause Analysis)

### Case #1: Ingestion Engine có chức năng gì? (Score 1.0)
1.  **Symptom (Triệu chứng):** Agent trả lời "Xin lỗi, tôi không có thông tin..."
2.  **Why 1:** LLM không thấy thông tin trong context truyền vào.
3.  **Why 2:** Khâu Retrieval trả về danh sách IDs không chứa `TECHNICAL_GUIDE_001`.
4.  **Why 3:** Hàm `_retrieve` sử dụng `q_tokens & tokens` (lexical overlap) không tìm thấy sự trùng khớp đủ lớn cho cụm từ chuyên môn.
5.  **Why 4:** Câu hỏi quá ngắn, các token chuyên môn bị biến đổi trong quá trình normalize/tokenize.
6.  **Root Cause:** **Hệ thống Retrieval hiện tại quá đơn giản (Keyword matching), thiếu Semantic Search (Vector Embedding) để hiểu ngữ nghĩa.**

### Case #2: Gói Basic sử dụng mô hình nào? (Score 1.0)
1.  **Symptom:** Agent trả lời "Không biết" trong khi Ground Truth là "GPT-3.5 Turbo".
2.  **Why 1:** Retrieval bị miss hoàn toàn tài liệu `PRODUCT_CATALOG`.
3.  **Why 2:** Logic tìm kiếm ID trực tiếp (`explicit_ids`) thất bại vì câu hỏi không chứa mã ID (như PROD_001).
4.  **Why 3:** Từ khóa "Basic" và "mô hình" không đủ trọng số để cạnh tranh với các chunk khác trong bộ máy Lexical.
5.  **Root Cause:** **Sự phụ thuộc quá lớn vào việc trùng khớp từ khóa thuần túy dẫn đến độ phủ (Recall) cực thấp.**

---

## 4. Kế hoạch cải tiến (Action Plan)

Dựa trên chỉ số **Hit Rate rất thấp (34%)**, nhóm đề xuất lộ trình tối ưu như sau:

1.  **Nâng cấp Retrieval (Ưu tiên 1):** 
    *   Chuyển từ Lexical Search (Token Overlap) sang **Hybrid Search** (Kết hợp Keyword + Vector Embedding). 
    *   Sử dụng `text-embedding-3-small` để xử lý các câu hỏi mang tính ngữ nghĩa thay vì chỉ bắt từ khóa.
2.  **Cải thiện Chunking strategy:**
    *   Hiện tại các bullet points bị chia nhỏ thành từng chunk riêng biệt (ví dụ: mỗi dòng giá là 1 chunk). Điều này làm mất ngữ cảnh bao quát. 
    *   Giải pháp: Gộp các bullet points liên quan vào cùng 1 chunk lớn hơn.
3.  **Cấu hình lại Agent Fallback:**
    *   Thay vì để Agent tự trả lời "Theo tài liệu:..." khi không có LLM, cần cải thiện prompt để Agent biết cách kết hợp các chunk vụn vặt tốt hơn.
4.  **Tối ưu Chi phí:**
    *   Sử dụng V1 (gpt-4o-mini) làm "Router" để phân loại câu hỏi. Chỉ gửi các câu hỏi khó cho V2 (gpt-4o) để giảm 40% chi phí nhưng vẫn giữ được mức điểm 3.95.

---
**Thay mặt nhóm thực hiện:** Trần Quang Long (QA/DevOps)  
**Ngày báo cáo:** 21/04/2026