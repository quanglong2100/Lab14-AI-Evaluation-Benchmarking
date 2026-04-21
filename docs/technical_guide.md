# Hướng dẫn Kỹ thuật: Hệ thống RAG Pipeline (v2.1)

## 1. Kiến trúc Hệ thống Tổng thể
Hệ thống RAG (Retrieval-Augmented Generation) của AI Global được thiết kế theo kiến trúc Microservices, cho phép mở rộng linh hoạt từng thành phần. Các khối chức năng chính bao gồm:
- **Ingestion Engine**: Chịu trách nhiệm thu thập dữ liệu từ các nguồn (Slack, Jira, Google Drive), thực hiện làm sạch văn bản (text cleaning) và chunking.
- **Embedding Service**: Sử dụng queue để xử lý song song việc tạo vector embeddings từ các khối văn bản.
- **Vector Database**: Lưu trữ và tìm kiếm vector không gian (semantic search). Hiện tại đang sử dụng ChromaDB cho môi trường staging và Pinecone cho môi trường production.
- **Reranker Module**: Một bước bổ sung sau retrieval để sắp xếp lại top-k kết quả dựa trên độ liên quan sâu hơn (Cross-encoding). (ID: TECH_001)

## 2. Công nghệ và Cấu hình Model
- **Embedding Model**: `text-embedding-3-small` (kích thước vector: 1536). Chúng ta chọn model này vì sự cân bằng giữa độ chính xác và chi phí.
- **LLM Engine**:
    - `gpt-4o-mini`: Dùng cho các tác vụ trả lời câu hỏi thông thường và phân loại (classification).
    - `gpt-4o`: Dùng cho các tác vụ phân tích phức tạp, trích xuất dữ liệu có cấu trúc từ văn bản không cấu trúc. (ID: TECH_002)
- **Framework**: LangChain kết hợp với LangGraph để quản lý trạng thái hội thoại.

## 3. Chiến lược Chunking và Tiền xử lý
- **Chunk Size**: 512 tokens (tương đương khoảng 600-800 từ tiếng Việt).
- **Chunk Overlap**: 10% (khoảng 50 tokens) để đảm bảo không mất ngữ cảnh ở các điểm cắt.
- **Splitting Strategy**: Sử dụng `RecursiveCharacterTextSplitter` với các separators theo thứ tự: `["\n\n", "\n", ".", " ", ""]`. (ID: TECH_003)
- **Metadata Tagging**: Mỗi chunk được gắn kèm các metadata: `source_url`, `author`, `last_updated`, và `security_level`. (ID: TECH_004)

## 4. Evaluation Metrics (Chỉ số đánh giá)
Để đảm bảo chất lượng hệ thống, chúng ta áp dụng bộ chỉ số RAGAS:
- **Faithfulness**: Đo lường mức độ câu trả lời trung thành với context (không bịa đặt).
- **Answer Relevancy**: Đo lường mức độ câu trả lời giải quyết được câu hỏi của người dùng.
- **Context Precision**: Đo lường chất lượng của các chunks được tìm kiếm thấy. (ID: TECH_005)
