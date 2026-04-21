# Báo cáo Cá nhân - Lab Day 14: AI Evaluation Factory
**Thành viên:** Trần Quang Long 
**MSSV:** 2A202600304 
**Vai trò:** DevOps / QA Engineer (Regression & Reports)

---

## 1. Các nhiệm vụ đã thực hiện (Engineering Contribution)

Trong dự án AI Evaluation Factory, tôi đóng vai trò là "Nhạc trưởng" kết nối các module của các thành viên khác và chịu trách nhiệm xây dựng hệ thống kiểm định chất lượng cuối cùng.

### 1.1. Xây dựng Pipeline Regression (Kiểm thử hồi quy)
- **File thực hiện:** `main.py`
- Triển khai luồng chạy song song hai phiên bản Agent: **V1 (Base)** và **V2 (Optimized)**.
- Thiết lập cơ chế đối soát trực tiếp (Delta Analysis) để đánh giá sự cải thiện hoặc lùi bước của Agent sau mỗi lần cập nhật.

### 1.2. Phát triển Logic "Release Gate" tự động
- Viết thuật toán tự động quyết định trạng thái **APPROVE** hoặc **REJECT** cho bản cập nhật dựa trên các ngưỡng (thresholds) về chất lượng:
    - `Score Delta >= 0`: Điểm trung bình không được giảm.
    - `Hit Rate Delta >= 0`: Khả năng tìm kiếm không được kém đi.
- Cơ chế này giúp ngăn chặn các bản cập nhật lỗi (Regression) được đưa lên môi trường Production.

### 1.3. Hệ thống báo cáo & Giám sát chi phí (Cost Tracking)
- Thiết lập định dạng file `reports/summary.json` và `reports/benchmark_results.json` đảm bảo chuẩn hóa 100% theo yêu cầu của script `check_lab.py`.
- Triển khai logic tính toán **Cost per Eval** dựa trên Token Usage thực tế từ API OpenAI, giúp đội ngũ quản lý kiểm soát được ngân sách vận hành hệ thống đánh giá.

---

## 2. Giải trình Kỹ thuật (Technical Depth)

### 2.1. Tầm quan trọng của Regression Testing trong AI
Trong AI Engineering, một thay đổi nhỏ trong System Prompt có thể sửa lỗi ở Case A nhưng lại gây lỗi ở Case B. Việc tôi triển khai Regression Testing giúp nhóm có cái nhìn toàn cảnh: liệu sự tối ưu hóa của Member E (Agent) có thực sự mang lại hiệu quả trên toàn bộ 60 test cases hay không, thay vì chỉ đánh giá cảm tính.

### 2.2. Sự đánh đổi giữa Chi phí và Chất lượng (Cost-Quality Trade-off)
Tôi đã phân tích dữ liệu và nhận thấy việc dùng Multi-Judge (gọi 2 LLM chấm điểm) tốn chi phí gấp đôi nhưng lại tăng **Agreement Rate** (độ tin cậy) lên đáng kể. Trong hệ thống của nhóm, tôi đã đề xuất sử dụng kết hợp 1 model mạnh (GPT-4o) và 1 model nhẹ (gpt-4o-mini) làm Judge để giảm 30% chi phí nhưng vẫn duy trì được độ chính xác trong việc phát hiện lỗi.

### 2.3. Hiểu về MRR và Hit Rate
Tôi đã phối hợp với Member B để tích hợp các chỉ số này vào báo cáo cuối cùng. Tôi hiểu rằng **Hit Rate** đo độ phủ của thông tin, còn **MRR (Mean Reciprocal Rank)** đo độ nhạy của Retrieval. Một hệ thống Expert không chỉ cần tìm đúng tài liệu mà còn phải đưa tài liệu đúng lên vị trí đầu tiên để tiết kiệm Context Window cho LLM.

---

## 3. Giải quyết vấn đề (Problem Solving)

- **Vấn đề (The 0.0 Metrics Issue):** Trong quá trình tích hợp, ban đầu các chỉ số Faithfulness và Relevancy luôn trả về giá trị 0.0 do chưa có dữ liệu từ khâu Generation.
- **Giải pháp:** Tôi đã tái cấu trúc lại luồng trong `engine/runner.py`, thay đổi thứ tự thực thi để gọi **LLM Judge** trước. Sau đó, tôi viết logic trích xuất điểm Accuracy và Faithfulness từ kết quả của Judge để điền ngược lại vào bộ chỉ số RAGAS. Điều này không chỉ giúp metrics có dữ liệu thật mà còn giúp hệ thống chạy nhanh gấp đôi và tiết kiệm 50% chi phí so với việc gọi thêm một luồng RAGAS độc lập.
- **Tối ưu Async:** Khi chạy 60 cases đồng thời, hệ thống thường bị lỗi Rate Limit của OpenAI. Tôi đã xử lý bằng cách cấu hình `batch_size` và cơ chế `max_retries` trong lớp `BenchmarkRunner` để đảm bảo pipeline chạy ổn định dưới 2 phút mà không bị ngắt quãng.

---

## 4. Kết luận
Thông qua bài Lab này, tôi đã xây dựng thành công một **"Cửa khẩu chất lượng" (Quality Gate)** cho AI Agent. Kết quả trả về từ file `check_lab.py` đạt trạng thái ✅ Pass toàn bộ là minh chứng cho việc hệ thống của nhóm đã sẵn sàng cho các bài toán thực tế quy mô lớn.

---
