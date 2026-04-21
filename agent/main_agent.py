import asyncio
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple

from openai import AsyncOpenAI

class MainAgent:
    """RAG agent for company policy, product catalog, and technical guide domain."""

    MODEL_PRICING = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 5.00, "output": 15.00},
    }
    def __init__(self):
        self.name = "AIGlobalSupportAgent-v3"
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.top_k = 3
        self.kb, self.id_to_source = self._load_domain_docs()
        self.doc_tokens: Dict[str, set] = {
            doc_id: set(self._tokenize(text)) for doc_id, text in self.kb.items()
        }

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.use_llm = bool(api_key)
        self.client = AsyncOpenAI(api_key=api_key) if self.use_llm else None

    def _load_domain_docs(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        root = Path(__file__).resolve().parents[1]
        docs_dir = root / "docs"
        files = [
            "company_policy.md",
            "product_catalog.md",
            "technical_guide.md",
        ]

        id_to_text: Dict[str, str] = {}
        id_to_source: Dict[str, str] = {}
        id_pattern = re.compile(r"\(ID:\s*([A-Z]+_\d+)\)")

        for filename in files:
            path = docs_dir / filename
            if not path.exists():
                continue
            content = path.read_text(encoding="utf-8")

            lines = content.splitlines()
            sections: List[str] = []
            current: List[str] = []
            for line in lines:
                if line.startswith("## ") and current:
                    sections.append("\n".join(current).strip())
                    current = [line]
                else:
                    current.append(line)
            if current:
                sections.append("\n".join(current).strip())

            for section in sections:
                found_ids = id_pattern.findall(section)
                if not found_ids:
                    continue
                section_lines = [ln.strip() for ln in section.splitlines() if ln.strip()]
                for found_id in found_ids:
                    hit_index = -1
                    marker = f"(ID: {found_id})"
                    for idx, line in enumerate(section_lines):
                        if marker in line:
                            hit_index = idx
                            break

                    if hit_index >= 0:
                        start = max(0, hit_index - 4)
                        end = min(len(section_lines), hit_index + 2)
                        snippet_lines = section_lines[start:end]
                        if section_lines and section_lines[0].startswith("##"):
                            snippet_lines = [section_lines[0]] + snippet_lines
                        snippet = "\n".join(snippet_lines)
                    else:
                        snippet = re.sub(r"\n{2,}", "\n", section).strip()

                    id_to_text[found_id] = snippet
                    id_to_source[found_id] = filename

        # Fallback entries keep agent functional even if IDs were not parsed.
        if not id_to_text:
            id_to_text = {
                "POL_001": "Nhan vien remote can online Slack va phan hoi tin nhan quan trong trong 15 phut.",
                "PROD_002": "Goi Pro gia 99$/thang, 10,000 requests/ngay, dung GPT-4o-mini va text-embedding-3-small.",
                "TECH_003": "Chunk size 512 tokens, overlap 10%, dung RecursiveCharacterTextSplitter.",
            }
            id_to_source = {
                "POL_001": "company_policy.md",
                "PROD_002": "product_catalog.md",
                "TECH_003": "technical_guide.md",
            }

        return id_to_text, id_to_source

    @staticmethod
    def _normalize(text: str) -> str:
        decomposed = unicodedata.normalize("NFD", text.lower())
        return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        normalized = MainAgent._normalize(text)
        return re.findall(r"[a-z0-9_]+", normalized)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, int(len(text.split()) * 1.3))

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING["gpt-4o-mini"])
        return (
            (input_tokens / 1_000_000) * pricing["input"]
            + (output_tokens / 1_000_000) * pricing["output"]
        )

    def _retrieve(self, question: str, top_k: int) -> Tuple[List[str], List[str]]:
        q_tokens = set(self._tokenize(question))
        explicit_ids = [doc_id for doc_id in re.findall(r"[A-Z]+_\d+", question.upper()) if doc_id in self.kb]

        # 1) Ưu tiên ID được nhắc trực tiếp trong câu hỏi.
        best: List[str] = []
        for doc_id in explicit_ids:
            if doc_id not in best:
                best.append(doc_id)
            if len(best) >= top_k:
                contexts = [self.kb.get(doc, "") for doc in best]
                return best, contexts

        # 2) Bổ sung bằng lexical overlap đơn giản.
        scored: List[Tuple[int, str]] = []
        for doc_id, d_tokens in self.doc_tokens.items():
            overlap = len(q_tokens & d_tokens)
            scored.append((overlap, doc_id))

        scored.sort(key=lambda x: x[0], reverse=True)
        for overlap, doc_id in scored:
            if overlap <= 0:
                continue
            if doc_id not in best:
                best.append(doc_id)
            if len(best) >= top_k:
                break

        # 3) Không match được gì thì trả rỗng để tránh retrieval sai.
        if not best:
            return [], []

        contexts = [self.kb.get(doc_id, "") for doc_id in best]
        return best, contexts

    def _is_ambiguous_question(self, question: str) -> bool:
        q_norm = self._normalize(question)
        has_price_intent = "gia" in q_norm
        has_plan_hint = any(term in q_norm for term in ["basic", "pro", "enterprise", "prod_001", "prod_002", "prod_003"])
        return has_price_intent and not has_plan_hint

    def _is_out_of_scope(self, question: str) -> bool:
        return False

    @staticmethod
    def _clean_context_excerpt(context: str) -> str:
        lines = [ln.strip() for ln in context.splitlines() if ln.strip()]
        cleaned: List[str] = []
        for ln in lines:
            ln = re.sub(r"^#+\s*", "", ln)
            ln = re.sub(r"^-\s*", "", ln)
            if ln:
                cleaned.append(ln)

        text = " ".join(cleaned)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            if len(sentence.strip()) >= 20:
                return sentence.strip()
        return text[:180].strip() if text else ""

    def _select_best_sentence(self, question: str, context: str) -> str:
        question_tokens = set(self._tokenize(question))
        lines = [ln.strip() for ln in context.splitlines() if ln.strip()]
        cleaned_lines = []
        for ln in lines:
            ln = re.sub(r"^#+\s*", "", ln)
            ln = re.sub(r"^-\s*", "", ln)
            cleaned_lines.append(ln)

        candidates = []
        for line in cleaned_lines:
            parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", line) if p.strip()]
            candidates.extend(parts)

        if not candidates:
            return ""

        best_sentence = candidates[0]
        best_score = -1.0
        for sentence in candidates:
            s_tokens = set(self._tokenize(sentence))
            overlap = len(question_tokens & s_tokens)
            bonus = 0.0
            if "$" in sentence or "VNĐ" in sentence or "GPT" in sentence or "tokens" in sentence:
                bonus += 0.2
            score = overlap + bonus
            if score > best_score:
                best_score = score
                best_sentence = sentence

        return best_sentence

    async def _generate_answer_with_llm(self, question: str, contexts: List[str]) -> Tuple[str, int, int, int]:
        context_blob = "\n\n".join(f"- {c}" for c in contexts)
        system_prompt = (
            "Ban la tro ly AI Global cho 3 mien: remote work policy, product catalog va technical RAG guide. "
            "Chi duoc tra loi dua tren context duoc cung cap. "
            "Neu context khong co thong tin thi noi ro: 'Khong tim thay thong tin trong tai lieu duoc cung cap'. "
            "Neu cau hoi mo ho thi yeu cau nguoi dung lam ro thay vi doan. "
            "Tra loi ngan gon, ro rang, bang tieng Viet co dau."
        )
        user_prompt = f"Cau hoi: {question}\n\nContext tham khao:\n{context_blob}"

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
            answer = "Không tìm thấy thông tin trong tài liệu được cung cấp."

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else self._estimate_tokens(system_prompt + user_prompt)
        output_tokens = usage.completion_tokens if usage else self._estimate_tokens(answer)
        total_tokens = usage.total_tokens if usage else (input_tokens + output_tokens)
        return answer, input_tokens, output_tokens, total_tokens

    def _generate_answer_fallback(self, question: str, contexts: List[str]) -> str:
        if self._is_out_of_scope(question):
            return "Không tìm thấy thông tin trong tài liệu được cung cấp."
        if self._is_ambiguous_question(question):
            return (
                "Bạn đang hỏi gói nào? Hiện có Basic, Pro và Enterprise. "
                "Vui lòng nêu rõ tên gói để mình trả lời chính xác về giá và tính năng."
            )
        if contexts:
            excerpt = self._select_best_sentence(question, contexts[0])
            if not excerpt:
                excerpt = self._clean_context_excerpt(contexts[0])
            if excerpt:
                return f"Theo tài liệu nội bộ, {excerpt}"
        return "Không tìm thấy thông tin trong tài liệu được cung cấp."

    async def query(self, question: str) -> Dict:
        start = time.perf_counter()

        if self._is_out_of_scope(question):
            retrieved_ids, contexts = [], []
        else:
            retrieved_ids, contexts = self._retrieve(question, self.top_k)
        llm_error = None

        if self.use_llm and self.client is not None:
            try:
                answer, input_tokens, output_tokens, total_tokens = await self._generate_answer_with_llm(question, contexts)
            except Exception as exc:
                llm_error = str(exc)
                answer = self._generate_answer_fallback(question, contexts)
                input_tokens = self._estimate_tokens(question + " " + " ".join(contexts))
                output_tokens = self._estimate_tokens(answer)
                total_tokens = input_tokens + output_tokens
        else:
            await asyncio.sleep(0)
            answer = self._generate_answer_fallback(question, contexts)
            input_tokens = self._estimate_tokens(question + " " + " ".join(contexts))
            output_tokens = self._estimate_tokens(answer)
            total_tokens = input_tokens + output_tokens

        estimated_cost_usd = self._estimate_cost(input_tokens, output_tokens)
        latency_ms = (time.perf_counter() - start) * 1000

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
                "estimated_cost_usd": round(estimated_cost_usd, 8),
                "latency_ms": round(latency_ms, 2),
                "sources": [self.id_to_source.get(doc_id, f"kb://{doc_id}") for doc_id in retrieved_ids],
                "llm_error": llm_error,
            }
        }

if __name__ == "__main__":
    agent = MainAgent()
    async def test():
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)
    asyncio.run(test())
