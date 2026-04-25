import os
import re
import unicodedata
from collections import defaultdict
from typing import Any, Dict, List, Optional

from legal_rag.config import (
    CHUNK_OVERLAP_TOKENS,
    DEFINITION_REGEX,
    EMBEDDING_MODEL_NAME,
    GENERIC_HEADING_REGEX,
    LEGAL_CHUNK_REGEX,
    MAX_CHUNK_TOKENS,
    STRUCTURE_CHUNK_REGEX,
)


class LegalChunker:
    STRUCTURE_PREFIX_REGEX = re.compile(r"^(phan|chuong|muc)\s+([ivxlcdm0-9]+)\b", re.IGNORECASE)
    ARTICLE_PREFIX_REGEX = re.compile(r"^dieu\s+(\d+)\b", re.IGNORECASE)

    def __init__(self):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        from transformers import AutoTokenizer

        self.legal_regex = re.compile(LEGAL_CHUNK_REGEX, re.MULTILINE)
        self.structure_regex = re.compile(STRUCTURE_CHUNK_REGEX, re.MULTILINE)
        self.generic_heading_regex = re.compile(GENERIC_HEADING_REGEX, re.MULTILINE)
        self.def_regex = re.compile(DEFINITION_REGEX, re.MULTILINE)
        self.tokenizer = AutoTokenizer.from_pretrained(
            EMBEDDING_MODEL_NAME,
            local_files_only=True,
            use_fast=True,
        )

    # ------------------------------------------------------------------ #
    # Text helpers                                                         #
    # ------------------------------------------------------------------ #

    def _strip_accents(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        normalized = normalized.replace("đ", "d").replace("Đ", "D")
        return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

    def _slugify(self, value: str, fallback: str = "chunk") -> str:
        folded = self._strip_accents(value).lower()
        folded = re.sub(r"[^a-z0-9]+", "_", folded).strip("_")
        return folded or fallback

    def _safe_id_component(self, value: str, fallback: str = "chunk") -> str:
        safe = value.strip().replace(":", "_")
        safe = re.sub(r"\s+", "_", safe)
        safe = re.sub(r"[<>]+", "_", safe)
        return safe or fallback

    # ------------------------------------------------------------------ #
    # Number helpers                                                       #
    # ------------------------------------------------------------------ #

    def _roman_to_int(self, value: str) -> Optional[int]:
        token = value.lower()
        if not token or re.search(r"[^ivxlcdm]", token):
            return None

        values = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
        total = 0
        previous = 0
        for char in reversed(token):
            current = values[char]
            if current < previous:
                total -= current
            else:
                total += current
                previous = current
        return total

    def _normalize_number_token(self, token: str) -> Optional[str]:
        stripped = token.strip().lower()
        if not stripped:
            return None
        if stripped.isdigit():
            return str(int(stripped))

        roman_value = self._roman_to_int(stripped)
        if roman_value is not None:
            return str(roman_value)
        return None

    # ------------------------------------------------------------------ #
    # Heading detection                                                    #
    # ------------------------------------------------------------------ #

    def _build_heading_marker(self, match: re.Match, level_hint: str) -> Dict[str, Any]:
        heading = (match.groupdict().get("heading") or match.group(0)).strip()
        normalized = self._strip_accents(heading).lower().strip()
        level = level_hint
        number = None

        structure_match = self.STRUCTURE_PREFIX_REGEX.match(normalized)
        if structure_match:
            keyword, token = structure_match.groups()
            level_map = {"phan": "part", "chuong": "chapter", "muc": "section"}
            level = level_map[keyword]
            number = self._normalize_number_token(token)
        else:
            article_match = self.ARTICLE_PREFIX_REGEX.match(normalized)
            if article_match:
                level = "article"
                number = self._normalize_number_token(article_match.group(1))
            elif normalized.startswith("dinh nghia") or normalized.startswith("giai thich tu ngu"):
                level = "definition"
            elif level_hint not in {"part", "chapter", "section", "article", "definition"}:
                level = "generic"

        return {
            "start": match.start(),
            "heading": heading,
            "level": level,
            "number": number,
        }

    def _collect_heading_markers(self, text: str) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for regex, hint in (
            (self.legal_regex, "article"),
            (self.structure_regex, "structure"),
            (self.def_regex, "definition"),
            (self.generic_heading_regex, "generic"),
        ):
            for match in regex.finditer(text):
                candidates.append(self._build_heading_marker(match, hint))

        priority = {
            "article": 0,
            "part": 1,
            "chapter": 1,
            "section": 1,
            "definition": 2,
            "generic": 3,
        }
        deduped: Dict[int, Dict[str, Any]] = {}
        for marker in sorted(candidates, key=lambda item: (item["start"], priority[item["level"]])):
            existing = deduped.get(marker["start"])
            if existing is None or priority[marker["level"]] < priority[existing["level"]]:
                deduped[marker["start"]] = marker

        return [deduped[start] for start in sorted(deduped)]

    def _select_chunk_markers(self, all_headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        article_markers = [marker for marker in all_headings if marker["level"] == "article"]
        if article_markers:
            return article_markers
        return all_headings

    # ------------------------------------------------------------------ #
    # Hierarchy metadata                                                   #
    # ------------------------------------------------------------------ #

    def _build_active_hierarchy(
        self,
        all_headings: List[Dict[str, Any]],
        start_index: int,
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        active: Dict[str, Optional[Dict[str, Any]]] = {
            "part": None,
            "chapter": None,
            "section": None,
        }
        for marker in all_headings:
            if marker["start"] > start_index:
                break

            level = marker["level"]
            if level == "part":
                active["part"] = marker
                active["chapter"] = None
                active["section"] = None
            elif level == "chapter":
                active["chapter"] = marker
                active["section"] = None
            elif level == "section":
                active["section"] = marker

        return active

    def _build_hierarchy_metadata(
        self,
        all_headings: List[Dict[str, Any]],
        marker: Optional[Dict[str, Any]],
        fallback_heading: str,
    ) -> tuple[str, str]:
        if marker is None:
            return fallback_heading, self._slugify(fallback_heading, fallback="chunk")

        active = self._build_active_hierarchy(all_headings, marker["start"])
        hierarchy_parts: List[str] = []
        logical_parts: List[str] = []
        for level, prefix in (("part", "phan"), ("chapter", "chuong"), ("section", "muc")):
            item = active[level]
            if item:
                hierarchy_parts.append(item["heading"])
                if item["number"]:
                    logical_parts.append(f"{prefix}_{item['number']}")

        if marker["level"] == "article":
            hierarchy_parts.append(marker["heading"])
            if marker["number"]:
                logical_parts.append(f"dieu_{marker['number']}")
        elif marker["level"] in {"definition", "generic"}:
            hierarchy_parts.append(marker["heading"])
            logical_parts.append(self._slugify(marker["heading"], fallback="section"))
        elif marker["level"] not in {"part", "chapter", "section"}:
            hierarchy_parts.append(marker["heading"])

        hierarchy_path = " > ".join(hierarchy_parts) if hierarchy_parts else fallback_heading
        logical_id = "_".join(logical_parts) if logical_parts else self._slugify(marker["heading"], fallback="chunk")
        return hierarchy_path, logical_id

    # ------------------------------------------------------------------ #
    # Token-based splitting                                                #
    # ------------------------------------------------------------------ #

    def _count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def _split_text_by_token_limit(self, text: str) -> List[str]:
        encoded = self.tokenizer(
            text,
            add_special_tokens=False,
            return_offsets_mapping=True,
            truncation=False,
        )
        offsets = encoded["offset_mapping"]
        if not offsets:
            return []

        if len(offsets) <= MAX_CHUNK_TOKENS:
            stripped = text.strip()
            return [stripped] if stripped else []

        parts: List[str] = []
        start_token = 0
        total_tokens = len(offsets)
        while start_token < total_tokens:
            end_token = min(total_tokens, start_token + MAX_CHUNK_TOKENS)
            char_start = offsets[start_token][0]
            char_end = offsets[end_token - 1][1]
            part = text[char_start:char_end].strip()
            if part:
                parts.append(part)

            if end_token >= total_tokens:
                break
            start_token = max(end_token - CHUNK_OVERLAP_TOKENS, start_token + 1)

        return parts

    # ------------------------------------------------------------------ #
    # Chunk assembly                                                       #
    # ------------------------------------------------------------------ #

    def _append_with_size_guard(
        self,
        target: List[Dict[str, Any]],
        chunk_content: str,
        metadata: Dict[str, Any],
    ) -> None:
        if self._count_tokens(chunk_content) <= MAX_CHUNK_TOKENS:
            target.append({"content": chunk_content, "metadata": metadata.copy()})
            return

        for part in self._split_text_by_token_limit(chunk_content):
            target.append({"content": part, "metadata": metadata.copy()})

    def _fallback_chunk_by_tokens(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not text:
            return []

        chunks: List[Dict[str, Any]] = []
        for idx, chunk_content in enumerate(self._split_text_by_token_limit(text), start=1):
            chunk_heading = f"Doan {idx}"
            chunk_meta = metadata.copy()
            chunk_meta.update(
                {
                    "chunk_heading": chunk_heading,
                    "hierarchy_path": chunk_heading,
                    "logical_id": self._slugify(chunk_heading, fallback=f"chunk_{idx}"),
                }
            )
            chunks.append({"content": chunk_content, "metadata": chunk_meta})

        return chunks

    def _split_by_markers(
        self,
        text: str,
        metadata: Dict[str, Any],
        markers: List[Dict[str, Any]],
        all_headings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []

        first_start = markers[0]["start"]
        if first_start > 0:
            preface = text[:first_start].strip()
            if preface:
                preface_meta = metadata.copy()
                preface_meta.update(
                    {
                        "chunk_heading": "Mo dau",
                        "hierarchy_path": "Mo dau",
                        "logical_id": "mo_dau",
                    }
                )
                self._append_with_size_guard(chunks, preface, preface_meta)

        for idx, marker in enumerate(markers):
            start_index = marker["start"]
            end_index = markers[idx + 1]["start"] if idx + 1 < len(markers) else len(text)
            chunk_content = text[start_index:end_index].strip()
            if not chunk_content:
                continue

            body = chunk_content.removeprefix(marker["heading"]).strip()
            if not body and idx + 1 < len(markers):
                continue

            hierarchy_path, logical_id = self._build_hierarchy_metadata(
                all_headings=all_headings,
                marker=marker,
                fallback_heading=marker["heading"],
            )
            chunk_meta = metadata.copy()
            chunk_meta.update(
                {
                    "chunk_heading": marker["heading"],
                    "hierarchy_path": hierarchy_path,
                    "logical_id": logical_id,
                }
            )
            self._append_with_size_guard(chunks, chunk_content, chunk_meta)

        return chunks

    def _finalize_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logical_counters: defaultdict[str, int] = defaultdict(int)
        finalized: List[Dict[str, Any]] = []

        for chunk_index, chunk in enumerate(chunks, start=1):
            metadata = chunk["metadata"].copy()
            metadata["chunk_index"] = chunk_index

            logical_id = metadata["logical_id"]
            logical_counters[logical_id] += 1
            part_index = logical_counters[logical_id]

            chunk_id = ":".join(
                [
                    self._safe_id_component(str(metadata["doc_id"]), fallback="doc"),
                    self._safe_id_component(str(metadata["version"]), fallback="v1"),
                    logical_id,
                    f"p{part_index:02d}",
                ]
            )

            finalized.append(
                {
                    "id": chunk_id,
                    "content": chunk["content"],
                    "metadata": metadata,
                }
            )

        return finalized

    # ------------------------------------------------------------------ #
    # Public entry point                                                   #
    # ------------------------------------------------------------------ #

    def semantic_chunking(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        all_headings = self._collect_heading_markers(text)
        if not all_headings:
            return self._finalize_chunks(self._fallback_chunk_by_tokens(text, metadata))

        chunk_markers = self._select_chunk_markers(all_headings)
        chunks = self._split_by_markers(text, metadata, chunk_markers, all_headings)
        if chunks:
            return self._finalize_chunks(chunks)

        return self._finalize_chunks(self._fallback_chunk_by_tokens(text, metadata))
