from __future__ import annotations

import os
from typing import List, Sequence

import torch
import torch.nn.functional as F


class BGEEmbeddingModel:
    """
    Local embedding wrapper for BGE-M3.
    """

    def __init__(self, model_name: str, device: str) -> None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        self.model_name = model_name
        self.device = self._resolve_device(device)
        self.backend = "transformers"
        from transformers import AutoModel, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            local_files_only=True,
            use_fast=True,
        )
        self._model = AutoModel.from_pretrained(
            model_name,
            local_files_only=True,
        ).to(self.device)
        self._model.eval()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]:
        cleaned_texts = [text.strip() for text in texts if text and text.strip()]
        if not cleaned_texts:
            return []

        encoded = self._tokenizer(
            cleaned_texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}

        with torch.no_grad():
            outputs = self._model(**encoded)

        token_embeddings = outputs.last_hidden_state
        attention_mask = encoded["attention_mask"]
        pooled = self._mean_pool(token_embeddings, attention_mask)
        normalized = F.normalize(pooled, p=2, dim=1)
        return normalized.cpu().tolist()

    @staticmethod
    def _mean_pool(token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        masked_embeddings = token_embeddings * mask
        summed = masked_embeddings.sum(dim=1)
        counts = mask.sum(dim=1).clamp(min=1e-9)
        return summed / counts

    @staticmethod
    def _resolve_device(requested_device: str) -> str:
        if requested_device == "cuda" and not torch.cuda.is_available():
            return "cpu"
        return requested_device
