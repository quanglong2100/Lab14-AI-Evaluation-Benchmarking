import asyncio
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple

from openai import AsyncOpenAI


class MainAgent:
    """RAG agent using prebuilt chunks + alias resolution."""

    MODEL_PRICING = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 5.00, "output": 15.00},
    }

    def __init__(self):
        self.name = "AIGlobalSupportAgent-v4"
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.top_k = 3

        # Load data
        self.kb, self.id_to_source = self._load_chunks()
        self.aliases = self._load_aliases()

        # Token index
        self.doc_tokens: Dict[str, set] = {
            doc_id: set(self._tokenize(text)) for doc_id, text in self.kb.items()
        }

        # LLM setup
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.use_llm = bool(api_key)
        self.client = AsyncOpenAI(api_key=api_key) if self.use_llm else None

    # --------------------------
    # LOAD DATA
    # --------------------------
    def _load_chunks(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        root = Path(__file__).resolve().parents[1]
        path = root / "data" / "chunks.jsonl"

        if not path.exists():
            raise FileNotFoundError("Missing chunks.jsonl. Run data/chunker.py first.")

        id_to_text = {}
        id_to_source = {}

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                cid = rec["chunk_id"]
                id_to_text[cid] = rec["text"]
                id_to_source[cid] = rec.get("source", "unknown")

        return id_to_text, id_to_source

    def _load_aliases(self) -> Dict[str, str]:
        root = Path(__file__).resolve().parents[1]
        path = root / "data" / "aliases.json"

        if not path.exists():
            return {}

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # --------------------------
    # TEXT PROCESSING
    # --------------------------
    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize("NFD", text.lower())
        return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        text = MainAgent._normalize(text)
        return re.findall(r"[a-z0-9_]+", text)

    # --------------------------
    # COST
    # --------------------------
    def _estimate_tokens(self, text: str) -> int:
        return max(1, int(len(text.split()) * 1.3))

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self.MODEL_PRICING.get(
            self.model_name, self.MODEL_PRICING["gpt-4o-mini"]
        )
        return (
            (input_tokens / 1_000_000) * pricing["input"]
            + (output_tokens / 1_000_000) * pricing["output"]
        )

    # --------------------------
    # RETRIEVAL
    # --------------------------
    def _retrieve(self, question: str, top_k: int) -> Tuple[List[str], List[str]]:
        q_tokens = set(self._tokenize(question))

        # 1. Explicit ID (POL_001 → alias)
        explicit_ids = []
        for raw_id in re.findall(r"[A-Z_]+_\d+", question.upper()):
            resolved = self.aliases.get(raw_id, raw_id)
            if resolved in self.kb and resolved not in explicit_ids:
                explicit_ids.append(resolved)

        if explicit_ids:
            contexts = [self.kb[cid] for cid in explicit_ids[:top_k]]
            return explicit_ids[:top_k], contexts

        # 2. Lexical retrieval
        scored = []
        for doc_id, tokens in self.doc_tokens.items():
            overlap = len(q_tokens & tokens)
            scored.append((overlap, doc_id))

        scored.sort(reverse=True)

        best = []
        for score, doc_id in scored:
            if score <= 0:
                continue
            best.append(doc_id)
            if len(best) >= top_k:
                break

        # 3. fallback root docs
        if not best:
            root_docs = [cid for cid in self.kb if cid.endswith("_000")]
            contexts = [self.kb[c] for c in root_docs[:top_k]]
            return root_docs[:top_k], contexts

        contexts = [self.kb[cid] for cid in best]
        return best, contexts

    # --------------------------
    # ANSWER
    # --------------------------
    def _is_ambiguous(self, question: str) -> bool:
        q = self._normalize(question)
        return "gia" in q and not any(x in q for x in ["basic", "pro", "enterprise"])

    def _fallback_answer(self, question: str, contexts: List[str]) -> str:
        if self._is_ambiguous(question):
            return "Bạn đang hỏi gói nào (Basic, Pro, Enterprise)?"

        if contexts:
            return f"Theo tài liệu: {contexts[0][:200]}"

        return "Không tìm thấy thông tin."

    async def _llm_answer(
        self, question: str, contexts: List[str]
    ) -> Tuple[str, int, int, int]:

        context_blob = "\n\n".join(contexts)

        system_prompt = (
            "Bạn là trợ lý AI. Chỉ trả lời dựa trên context. "
            "Nếu không có thông tin thì nói không biết."
        )

        user_prompt = f"Câu hỏi: {question}\n\nContext:\n{context_blob}"

        response = await self.client.chat.completions.create(
            model=self.model_name,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        answer = (response.choices[0].message.content or "").strip()
        if not answer:
            answer = "Không tìm thấy thông tin."

        usage = response.usage
        input_tokens = (
            usage.prompt_tokens
            if usage
            else self._estimate_tokens(system_prompt + user_prompt)
        )
        output_tokens = (
            usage.completion_tokens
            if usage
            else self._estimate_tokens(answer)
        )
        total_tokens = usage.total_tokens if usage else input_tokens + output_tokens

        return answer, input_tokens, output_tokens, total_tokens

    # --------------------------
    # MAIN API
    # --------------------------
    async def query(self, question: str) -> Dict:
        start = time.perf_counter()

        retrieved_ids, contexts = self._retrieve(question, self.top_k)

        llm_error = None

        if self.use_llm and self.client:
            try:
                answer, input_tokens, output_tokens, total_tokens = (
                    await self._llm_answer(question, contexts)
                )
            except Exception as e:
                llm_error = str(e)
                answer = self._fallback_answer(question, contexts)
                input_tokens = self._estimate_tokens(question)
                output_tokens = self._estimate_tokens(answer)
                total_tokens = input_tokens + output_tokens
        else:
            await asyncio.sleep(0)
            answer = self._fallback_answer(question, contexts)
            input_tokens = self._estimate_tokens(question)
            output_tokens = self._estimate_tokens(answer)
            total_tokens = input_tokens + output_tokens

        cost = self._estimate_cost(input_tokens, output_tokens)
        latency = (time.perf_counter() - start) * 1000

        return {
            "answer": answer,
            "contexts": contexts,
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": self.model_name,
                "llm_enabled": self.use_llm,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": round(cost, 8),
                "latency_ms": round(latency, 2),
                "sources": [
                    self.id_to_source.get(doc_id, "unknown")
                    for doc_id in retrieved_ids
                ],
                "llm_error": llm_error,
            },
        }


# --------------------------
# TEST
# --------------------------
if __name__ == "__main__":
    agent = MainAgent()

    async def test():
        questions = [
            "POL_001 là gì?",
            "Giờ làm việc thế nào?",
            "Gói Pro có gì?",
            "Cách đổi mật khẩu?"
        ]

        for q in questions:
            print("\nQ:", q)
            res = await agent.query(q)
            print("A:", res["answer"])
            print("IDs:", res["retrieved_ids"])

    asyncio.run(test())