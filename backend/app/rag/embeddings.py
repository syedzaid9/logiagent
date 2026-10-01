import math
import numpy as np
from typing import List, Optional
from app.core.config import settings
from app.core.logging_config import logger

class EmbeddingsService:
    """
    Real Embedding Engine for LogiAgent RAG Pipeline.
    Supports local SentenceTransformers (all-MiniLM-L6-v2, 384-dim) and
    Google Gemini Embedding API (text-embedding-004, 768-dim).
    """

    def __init__(self):
        self._local_model = None
        self.model_type = (settings.EMBEDDING_MODEL_TYPE or "local").lower()
        self.gemini_key = settings.GEMINI_API_KEY
        self.embedding_dimension = settings.EMBEDDING_DIMENSION
        logger.info(f"[EmbeddingsService] Initialized with model_type='{self.model_type}', dimension={self.embedding_dimension}")

    def _get_local_model(self):
        if self._local_model is None:
            logger.info(f"[EmbeddingsService] Loading local embedding model: {settings.EMBEDDING_MODEL_NAME}...")
            try:
                from sentence_transformers import SentenceTransformer
                self._local_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                logger.info(f"[EmbeddingsService] Local embedding model loaded successfully.")
            except Exception as e:
                logger.error(f"[EmbeddingsService] Failed to load SentenceTransformer: {e}")
                # Fallback to transformers directly
                from transformers import AutoTokenizer, AutoModel
                import torch
                class SimpleHFEmbedder:
                    def __init__(self, name):
                        self.tokenizer = AutoTokenizer.from_pretrained(name)
                        self.model = AutoModel.from_pretrained(name)
                    def encode(self, texts, **kwargs):
                        if isinstance(texts, str):
                            texts = [texts]
                        inputs = self.tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
                        with torch.no_grad():
                            out = self.model(**inputs)
                            # Mean pooling
                            mask = inputs["attention_mask"].unsqueeze(-1).expand(out.last_hidden_state.size()).float()
                            sum_emb = torch.sum(out.last_hidden_state * mask, 1)
                            sum_mask = torch.clamp(mask.sum(1), min=1e-9)
                            pooled = sum_emb / sum_mask
                            return pooled.cpu().numpy()
                self._local_model = SimpleHFEmbedder(settings.EMBEDDING_MODEL_NAME)
                logger.info(f"[EmbeddingsService] Fallback HuggingFace embedder loaded successfully.")
        return self._local_model

    def _normalize(self, vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            return [x / norm for x in vec]
        return vec

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single query text."""
        clean_text = text.strip()
        if not clean_text:
            return [0.0] * self.embedding_dimension

        # 1. Gemini Embedding
        if self.model_type == "gemini" and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=clean_text,
                    task_type="retrieval_query"
                )
                raw_vec = res["embedding"]
                return self._normalize(raw_vec)
            except Exception as e:
                logger.warning(f"[EmbeddingsService] Gemini embedding failed: {e}. Falling back to local model.")

        # 2. Local SentenceTransformer
        model = self._get_local_model()
        emb = model.encode(clean_text)
        if isinstance(emb, np.ndarray):
            raw_vec = emb.flatten().tolist()
        elif hasattr(emb, "tolist"):
            raw_vec = emb.tolist()
        else:
            raw_vec = list(emb)
        return self._normalize(raw_vec)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of document chunks."""
        if not texts:
            return []

        clean_texts = [t.strip() if t.strip() else " " for t in texts]

        # 1. Gemini Batch Embedding
        if self.model_type == "gemini" and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=clean_texts,
                    task_type="retrieval_document"
                )
                embeddings = [self._normalize(v) for v in res["embedding"]]
                return embeddings
            except Exception as e:
                logger.warning(f"[EmbeddingsService] Gemini batch embedding failed: {e}. Falling back to local model.")

        # 2. Local SentenceTransformer
        model = self._get_local_model()
        embs = model.encode(clean_texts, show_progress_bar=False, batch_size=16)
        if isinstance(embs, np.ndarray):
            result = [self._normalize(embs[i].tolist()) for i in range(len(embs))]
        else:
            result = [self._normalize(list(v)) for v in embs]
        return result

embeddings_service = EmbeddingsService()
