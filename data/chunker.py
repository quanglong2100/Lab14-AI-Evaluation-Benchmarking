import json
import re
from pathlib import Path
from typing import Dict, List


class DocumentChunker:
    ROOT_IDS = {
        "company_policy.md": "COMPANY_POLICY_000",
        "product_catalog.md": "PRODUCT_CATALOG_000",
        "technical_guide.md": "TECHNICAL_GUIDE_000",
    }

    PREFIX = {
        "company_policy.md": "COMPANY_POLICY",
        "product_catalog.md": "PRODUCT_CATALOG",
        "technical_guide.md": "TECHNICAL_GUIDE",
    }

    def __init__(self):
        root = Path(__file__).resolve().parents[1]
        self.docs_dir = root / "docs"
        self.output_path = root / "data" / "chunks.jsonl"
        self.alias_path = root / "data" / "aliases.json"

    # -------------------
    # Utils
    # -------------------
    def _next_id(self, filename: str, counters: Dict[str, int]) -> str:
        prefix = self.PREFIX[filename]
        idx = counters.get(filename, 1)
        counters[filename] = idx + 1
        return f"{prefix}_{idx:03d}"

    def _split_sections(self, content: str) -> List[str]:
        return re.split(r"\n(?=## )", content)

    def _extract_ids(self, text: str) -> List[str]:
        return re.findall(r"\(ID:\s*([A-Z]+_\d+)\)", text)

    def _clean(self, text: str) -> str:
        return re.sub(r"\n{2,}", "\n", text).strip()

    def _split_bullets(self, section: str) -> List[str]:
        lines = [l.strip() for l in section.splitlines() if l.strip()]

        chunks = []
        current = []

        for line in lines:
            if line.startswith("- "):
                if current:
                    chunks.append("\n".join(current))
                current = [line]
            else:
                current.append(line)

        if current:
            chunks.append("\n".join(current))

        return chunks

    # -------------------
    # Main
    # -------------------
    def build(self):
        records = []
        counters = {}
        alias_map = {}
        seen = set()

        for filename in self.ROOT_IDS:
            path = self.docs_dir / filename
            if not path.exists():
                continue

            content = path.read_text(encoding="utf-8")

            # ROOT
            title = content.splitlines()[0].strip()
            records.append({
                "chunk_id": self.ROOT_IDS[filename],
                "source": filename,
                "section": "root",
                "text": title
            })

            sections = self._split_sections(content)

            for sec in sections:
                sec = self._clean(sec)
                if not sec:
                    continue

                ids = self._extract_ids(sec)
                chunks = self._split_bullets(sec)

                for chunk in chunks:
                    chunk = self._clean(chunk)

                    if chunk in seen:
                        continue
                    seen.add(chunk)

                    cid = self._next_id(filename, counters)

                    # map alias
                    for rid in ids:
                        alias_map[rid] = cid

                    records.append({
                        "chunk_id": cid,
                        "source": filename,
                        "section": sec.split("\n")[0].replace("##", "").strip(),
                        "text": chunk
                    })

        return records, alias_map

    def save(self):
        records, alias_map = self.build()

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        with open(self.alias_path, "w", encoding="utf-8") as f:
            json.dump(alias_map, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(records)} chunks")
        print(f"Saved aliases: {len(alias_map)}")


if __name__ == "__main__":
    DocumentChunker().save()