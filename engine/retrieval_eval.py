from typing import List, Dict, Tuple
import math


class RetrievalEvaluator:
    """
    Đánh giá chất lượng của Retrieval stage trong RAG pipeline.

    Hai chỉ số chính:
    - Hit Rate@K : Có ít nhất 1 document đúng trong Top-K kết quả không?
    - MRR (Mean Reciprocal Rank): Document đúng xuất hiện ở vị trí bao nhiêu?
    """

    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    # ------------------------------------------------------------------
    # Single-case metrics
    # ------------------------------------------------------------------

    def calculate_hit_rate(
        self,
        expected_ids: List[str],
        retrieved_ids: List[str],
        top_k: int = None,
    ) -> float:
        """
        Hit Rate@K = 1 nếu ít nhất 1 ID trong expected_ids xuất hiện
        trong top_k đầu tiên của retrieved_ids, ngược lại = 0.

        Args:
            expected_ids: Danh sách ID chunk được coi là đúng (Ground Truth).
            retrieved_ids: Danh sách ID chunk Agent trả về (theo thứ tự ưu tiên).
            top_k: Số kết quả đầu cần xét. Mặc định dùng self.top_k.

        Returns:
            1.0 (hit) hoặc 0.0 (miss).

        Example:
            >>> ev = RetrievalEvaluator(top_k=3)
            >>> ev.calculate_hit_rate(["POL_001"], ["POL_002", "POL_001", "TECH_003"])
            1.0   # POL_001 nằm ở vị trí 2 (trong top-3)
        """
        k = top_k if top_k is not None else self.top_k

        if not expected_ids:
            # Không có ground truth → không cần truy xuất → hit mặc định
            return 1.0

        top_retrieved = retrieved_ids[:k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(
        self,
        expected_ids: List[str],
        retrieved_ids: List[str],
    ) -> float:
        """
        Mean Reciprocal Rank (MRR) cho một query.

        MRR = 1 / rank(first_hit), với rank là vị trí 1-indexed.
        Nếu không có expected_id nào trong retrieved_ids → MRR = 0.

        Args:
            expected_ids: Danh sách ID chunk được coi là đúng (Ground Truth).
            retrieved_ids: Danh sách ID chunk Agent trả về.

        Returns:
            Float trong khoảng [0, 1].

        Example:
            >>> ev = RetrievalEvaluator()
            >>> ev.calculate_mrr(["POL_001"], ["TECH_001", "POL_001", "PROD_002"])
            0.5   # POL_001 ở vị trí 2 → 1/2 = 0.5
        """
        if not expected_ids:
            return 1.0  # không cần truy xuất → perfect

        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in expected_ids:
                return 1.0 / rank
        return 0.0

    def calculate_precision_at_k(
        self,
        expected_ids: List[str],
        retrieved_ids: List[str],
        top_k: int = None,
    ) -> float:
        """
        Precision@K = (số ID đúng trong top-K) / K

        Args:
            expected_ids: Ground Truth IDs.
            retrieved_ids: Retrieved IDs.
            top_k: Số kết quả xét.

        Returns:
            Float trong [0, 1].
        """
        k = top_k if top_k is not None else self.top_k
        if not expected_ids or k == 0:
            return 0.0
        top_retrieved = retrieved_ids[:k]
        hits = sum(1 for doc_id in top_retrieved if doc_id in expected_ids)
        return hits / k

    # ------------------------------------------------------------------
    # Batch evaluation
    # ------------------------------------------------------------------

    async def evaluate_batch(self, dataset: List[Dict]) -> Dict:
        """
        Chạy eval toàn bộ dataset và tổng hợp metrics.

        Mỗi item trong dataset cần có:
        - `expected_retrieval_ids` (List[str]): Ground Truth chunk IDs.
        - `retrieved_ids` (List[str]): Chunk IDs mà Agent đã truy xuất.

        Returns dict với:
        - avg_hit_rate    : Trung bình Hit Rate@K
        - avg_mrr         : Trung bình MRR
        - avg_precision_k : Trung bình Precision@K
        - total           : Tổng số cases
        - passed          : Số cases có hit_rate == 1
        - failed          : Số cases có hit_rate == 0
        - per_case_details: List kết quả từng case (để debug)
        """
        hit_rates, mrrs, precisions = [], [], []
        per_case_details = []

        for item in dataset:
            expected = item.get("expected_retrieval_ids", [])
            retrieved = item.get("retrieved_ids", [])

            hr = self.calculate_hit_rate(expected, retrieved)
            mrr = self.calculate_mrr(expected, retrieved)
            prec = self.calculate_precision_at_k(expected, retrieved)

            hit_rates.append(hr)
            mrrs.append(mrr)
            precisions.append(prec)

            per_case_details.append({
                "question": item.get("question", ""),
                "expected_ids": expected,
                "retrieved_ids": retrieved[:self.top_k],
                "hit_rate": hr,
                "mrr": round(mrr, 4),
                "precision_at_k": round(prec, 4),
                "status": "pass" if hr == 1.0 else "fail",
            })

        total = len(dataset)
        passed = sum(1 for h in hit_rates if h == 1.0)
        avg_hr = sum(hit_rates) / total if total else 0.0
        avg_mrr = sum(mrrs) / total if total else 0.0
        avg_prec = sum(precisions) / total if total else 0.0

        return {
            "avg_hit_rate": round(avg_hr, 4),
            "avg_mrr": round(avg_mrr, 4),
            "avg_precision_at_k": round(avg_prec, 4),
            "top_k": self.top_k,
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "per_case_details": per_case_details,
        }

    def print_report(self, results: Dict) -> None:
        """In báo cáo retrieval đẹp ra console."""
        print("\n" + "=" * 50)
        print("📊 RETRIEVAL EVALUATION REPORT")
        print("=" * 50)
        print(f"  Top-K           : {results['top_k']}")
        print(f"  Total cases     : {results['total']}")
        print(f"  Passed (hit)    : {results['passed']}")
        print(f"  Failed (miss)   : {results['failed']}")
        print(f"  Hit Rate@{results['top_k']}     : {results['avg_hit_rate']*100:.1f}%")
        print(f"  MRR             : {results['avg_mrr']:.4f}")
        print(f"  Precision@{results['top_k']}    : {results['avg_precision_at_k']*100:.1f}%")
        print("=" * 50)

        # Top 5 cases bị miss
        failed_cases = [c for c in results["per_case_details"] if c["status"] == "fail"]
        if failed_cases:
            print(f"\n❌ {len(failed_cases)} cases bị MISS (hiển thị tối đa 5):")
            for case in failed_cases[:5]:
                print(f"   Q: {case['question'][:70]}...")
                print(f"      Expected : {case['expected_ids']}")
                print(f"      Retrieved: {case['retrieved_ids']}")
        else:
            print("\n✅ Tất cả cases đều HIT!")


# -------------------------------------------------------------------------
# Quick test khi chạy trực tiếp
# -------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio

    evaluator = RetrievalEvaluator(top_k=3)

    # Dữ liệu test
    mock_dataset = [
        {
            "question": "Chunk size hệ thống là bao nhiêu?",
            "expected_retrieval_ids": ["TECH_003"],
            "retrieved_ids": ["TECH_003", "TECH_001", "POL_002"],
        },
        {
            "question": "Gói Pro có giá bao nhiêu?",
            "expected_retrieval_ids": ["PROD_002"],
            "retrieved_ids": ["PROD_001", "PROD_003", "TECH_002"],   # MISS
        },
        {
            "question": "Thời gian phản hồi trên Slack là bao lâu?",
            "expected_retrieval_ids": ["POL_001"],
            "retrieved_ids": ["TECH_001", "POL_001", "PROD_002"],
        },
        {
            "question": "Adversarial: câu ngoài context",
            "expected_retrieval_ids": [],
            "retrieved_ids": [],
        },
    ]

    results = asyncio.run(evaluator.evaluate_batch(mock_dataset))
    evaluator.print_report(results)

    # Kiểm tra từng hàm riêng lẻ
    print("\n--- Unit tests ---")
    ev = RetrievalEvaluator()
    assert ev.calculate_hit_rate(["A"], ["A", "B", "C"]) == 1.0,   "Hit rate test 1 failed"
    assert ev.calculate_hit_rate(["A"], ["B", "C", "D"]) == 0.0,   "Hit rate test 2 failed"
    assert ev.calculate_hit_rate(["A"], ["B", "A", "C"], top_k=1) == 0.0, "Top-1 miss failed"
    assert ev.calculate_mrr(["A"], ["A", "B"]) == 1.0,             "MRR rank-1 failed"
    assert ev.calculate_mrr(["A"], ["B", "A"]) == 0.5,             "MRR rank-2 failed"
    assert ev.calculate_mrr(["A"], ["B", "C"]) == 0.0,             "MRR not-found failed"
    print("✅ Tất cả unit tests đều PASSED!")
